"""CLI command groups — thin API consumers using httpx + rich."""

from __future__ import annotations

from orgbrain.cli.commands.domain import domain_app
from orgbrain.cli.commands.extract import extract_app
from orgbrain.cli.commands.query import query_app
from orgbrain.cli.commands.repo import repo_app
from orgbrain.cli.commands.token import token_app

__all__ = ["domain_app", "extract_app", "query_app", "repo_app", "token_app"]
