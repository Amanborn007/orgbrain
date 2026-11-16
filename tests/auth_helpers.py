"""Shared builders for the roles / API-token / identity-hardening tests."""

from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from orgbrain.cli.config import reset_settings

_IDENTITY_ENV = (
    "ORGBRAIN_DEMO_MODE",
    "ORGBRAIN_OPERATOR_EMAIL",
    "ORGBRAIN_OPERATOR_GROUPS",
    "ORGBRAIN_API_TOKENS",
    "ORGBRAIN_IDENTITY__PROVIDER",
    "ORGBRAIN_IDENTITY__TRUSTED_PROXY",
    "ORGBRAIN_IDENTITY__ROLES",
    "ORGBRAIN_IDENTITY__HEADER",
    "ORGBRAIN_IDENTITY__HEADER__EMAIL",
    "ORGBRAIN_IDENTITY__HEADER__GROUPS",
    "ORGBRAIN_IDENTITY__HEADER__TRUSTED_PROXY_CIDRS",
    "ORGBRAIN_IDENTITY__OIDC__JWKS_URL",
    "ORGBRAIN_IDENTITY__OIDC__ISSUER",
    "ORGBRAIN_IDENTITY__OIDC__AUDIENCE",
    "ORGBRAIN_IDENTITY__OIDC__GROUPS_CLAIM",
    "ORGBRAIN_TOKEN",
)

JWKS_URL = "https://idp.example.com/.well-known/jwks.json"
ISSUER = "https://idp.example.com/"
AUDIENCE = "orgbrain"


def new_token() -> tuple[str, str]:
    """A fresh ``bft_`` token and its sha256 hex digest."""
    token = "bft_" + secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()


def token_entry(name: str, token: str, roles: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "sha256": hashlib.sha256(token.encode()).hexdigest(),
        "roles": roles if roles is not None else ["member"],
    }


def boot(
    monkeypatch: pytest.MonkeyPatch,
    *,
    provider: str = "none",
    roles: dict[str, list[str]] | None = None,
    tokens: list[dict[str, Any]] | None = None,
    demo: bool | None = None,
    operator_email: str | None = None,
    cidrs: list[str] | None = None,
    groups_header: str | None = None,
    email_header: str | None = None,
    oidc: bool = False,
    extra_env: dict[str, str] | None = None,
) -> FastAPI:
    """Reset identity env, apply the given config, and build the app."""
    for key in _IDENTITY_ENV:
        monkeypatch.delenv(key, raising=False)
    if demo is None:
        demo = provider == "none" and operator_email is None
    monkeypatch.setenv("ORGBRAIN_DEMO_MODE", "true" if demo else "false")
    monkeypatch.setenv("ORGBRAIN_IDENTITY__PROVIDER", provider)
    if provider == "header":
        monkeypatch.setenv("ORGBRAIN_IDENTITY__TRUSTED_PROXY", "true")
    if operator_email:
        monkeypatch.setenv("ORGBRAIN_OPERATOR_EMAIL", operator_email)
    if roles is not None:
        monkeypatch.setenv("ORGBRAIN_IDENTITY__ROLES", json.dumps(roles))
    if tokens is not None:
        monkeypatch.setenv("ORGBRAIN_API_TOKENS", json.dumps(tokens))
    if cidrs is not None:
        monkeypatch.setenv("ORGBRAIN_IDENTITY__HEADER__TRUSTED_PROXY_CIDRS", json.dumps(cidrs))
    if groups_header:
        monkeypatch.setenv("ORGBRAIN_IDENTITY__HEADER__GROUPS", groups_header)
    if email_header:
        monkeypatch.setenv("ORGBRAIN_IDENTITY__HEADER__EMAIL", email_header)
    if oidc or provider == "oidc_jwt":
        monkeypatch.setenv("ORGBRAIN_IDENTITY__OIDC__JWKS_URL", JWKS_URL)
        monkeypatch.setenv("ORGBRAIN_IDENTITY__OIDC__ISSUER", ISSUER)
        monkeypatch.setenv("ORGBRAIN_IDENTITY__OIDC__AUDIENCE", AUDIENCE)
    for key, value in (extra_env or {}).items():
        monkeypatch.setenv(key, value)
    reset_settings()
    from orgbrain.api.app import create_app

    return create_app()


def client(app: FastAPI, host: str = "127.0.0.1") -> AsyncClient:
    """An in-process client whose ASGI peer address is ``host``."""
    transport = ASGITransport(app=app, client=(host, 4242))
    return AsyncClient(transport=transport, base_url="http://t")


def header_identity(email: str, groups: str = "") -> dict[str, str]:
    headers = {"X-Forwarded-Email": email}
    if groups:
        headers["X-Forwarded-Groups"] = groups
    return headers
