"""orgbrain.yaml configuration: loading, precedence, defaults, validation, helpers."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from orgbrain.cli.config import OrgBrainSettings
from orgbrain.cli.config_sections import (
    ConventionsConfig,
    IdentityConfig,
    JiraSourceConfig,
    ManifestConfig,
    McpConfig,
)
from orgbrain.errors import ConfigError

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_MCP_PREFIXES = {
    "atlassian": "mcp__atlassian__",
    "github": "mcp__github__",
    "slack": "mcp__claude_ai_Slack__",
    "slack_write": "mcp__plugin_slack_slack__",
    "gdrive": "mcp__claude_ai_Google_Drive__",
}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run in an empty CWD with no ORGBRAIN_CONFIG and no nested ORGBRAIN_* overrides."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ORGBRAIN_CONFIG", "")
    for key in list(os.environ):
        if key.startswith(
            (
                "ORGBRAIN_ORG",
                "ORGBRAIN_SOURCES",
                "ORGBRAIN_MCP",
                "ORGBRAIN_MANIFEST",
                "ORGBRAIN_LINKING",
                "ORGBRAIN_CONVENTIONS",
                "ORGBRAIN_IDENTITY",
            )
        ):
            monkeypatch.delenv(key)


def _write(tmp_path: Path, text: str, name: str = "orgbrain.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# ── Loading ──────────────────────────────────────────────────────────


def test_yaml_loads_via_orgbrain_config_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        "org:\n  name: widgetco\nsources:\n  github:\n    host: ghe.example.com\n",
        "custom.yaml",
    )
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(path))
    s = OrgBrainSettings()
    assert s.org.name == "widgetco"
    assert s.sources.github.host == "ghe.example.com"


def test_empty_orgbrain_config_means_no_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write(tmp_path, "org:\n  name: ignored\n")
    monkeypatch.setenv("ORGBRAIN_CONFIG", "")
    assert OrgBrainSettings().org.name == ""


def test_missing_configured_path_raises_config_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "nope.yaml"
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(missing))
    with pytest.raises(ConfigError, match="nope.yaml"):
        OrgBrainSettings()


def test_cwd_orgbrain_yaml_used_when_env_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write(tmp_path, "org:\n  name: from-cwd\n")
    monkeypatch.delenv("ORGBRAIN_CONFIG")
    assert OrgBrainSettings().org.name == "from-cwd"


def test_no_file_and_env_unset_uses_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ORGBRAIN_CONFIG")
    assert OrgBrainSettings().org.name == ""


# ── Precedence: init kwargs > env > .env > YAML > defaults ──────────


def test_precedence_chain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = _write(tmp_path, "org:\n  name: yaml\n", "custom.yaml")
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(path))
    assert OrgBrainSettings().org.name == "yaml"

    (tmp_path / ".env").write_text("ORGBRAIN_ORG__NAME=dotenv\n", encoding="utf-8")
    assert OrgBrainSettings().org.name == "dotenv"

    monkeypatch.setenv("ORGBRAIN_ORG__NAME", "env")
    assert OrgBrainSettings().org.name == "env"

    assert OrgBrainSettings(org={"name": "init"}).org.name == "init"


def test_nested_env_overrides_yaml_and_keeps_siblings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        "sources:\n  jira:\n    base_url: https://yaml.example.com\n  github:\n    host: ghe.example.com\n",
        "custom.yaml",
    )
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(path))
    monkeypatch.setenv("ORGBRAIN_SOURCES__JIRA__BASE_URL", "https://env.example.com")
    s = OrgBrainSettings()
    assert s.sources.jira.base_url == "https://env.example.com"
    assert s.sources.github.host == "ghe.example.com"


def test_flat_env_vars_still_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORGBRAIN_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ORGBRAIN_MAX_CONCURRENT_CLI_CALLS", "7")
    s = OrgBrainSettings()
    assert s.log_level == "DEBUG"
    assert s.max_concurrent_cli_calls == 7


# ── Defaults ─────────────────────────────────────────────────────────


def test_section_defaults() -> None:
    s = OrgBrainSettings()
    assert s.org.name == ""
    assert s.sources.github.host == "github.com"
    assert s.sources.github.orgs == []
    assert s.sources.jira.base_url == ""
    assert s.sources.local.allowed_roots == []
    assert s.manifest.providers == ["backstage", "codeowners"]
    assert s.linking.internal_package_prefixes == []
    assert s.identity.provider == "none"


def test_mcp_tool_prefix_defaults() -> None:
    assert OrgBrainSettings().mcp.tool_prefix == EXPECTED_MCP_PREFIXES


def test_conventions_defaults() -> None:
    c = OrgBrainSettings().conventions
    assert c.jira_project_key == "{TEAM}"
    assert c.confluence_space_key == "{TEAM}"
    assert c.slack_channel == "#{team}"
    assert c.placeholder_teams == []


def test_manifest_section_shape() -> None:
    m = OrgBrainSettings().manifest
    assert m.config_globs == [
        "config/*.env",
        ".env.example",
        "docker-compose*.y*ml",
        "helm/**/values*.yaml",
        "charts/**/values*.yaml",
    ]
    assert m.remote_config_globs is False
    assert m.max_file_bytes == 262144
    assert m.backstage.paths == ["catalog-info.yaml", "catalog-info.yml"]
    assert m.backstage.annotation_map == {}
    assert m.backstage.label_map == {}
    assert m.codeowners.paths == ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]
    assert m.codeowners.strip_org_prefix is True
    assert m.generic_yaml.path == ""
    assert m.generic_yaml.fields == {}
    assert m.generic_yaml.config_blocks == []


def test_mutable_defaults_are_not_shared() -> None:
    a, b = OrgBrainSettings(), OrgBrainSettings()
    a.sources.github.orgs.append("x")
    assert b.sources.github.orgs == []


# ── Validation ───────────────────────────────────────────────────────


def test_unknown_manifest_provider_rejected() -> None:
    with pytest.raises(ValidationError, match="nonsense"):
        ManifestConfig(providers=["backstage", "nonsense"])


def test_unknown_identity_provider_rejected() -> None:
    with pytest.raises(ValidationError, match="ldap"):
        IdentityConfig(provider="ldap")


@pytest.mark.parametrize(
    "bad", ["atlassian", "mcp__atlassian", "mcp__atlassian_", "mcp____", "mcp__a b__"]
)
def test_mcp_prefix_must_match_pattern(bad: str) -> None:
    with pytest.raises(ValidationError):
        McpConfig(tool_prefix={"atlassian": bad})


def test_invalid_yaml_value_fails_settings_construction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = _write(tmp_path, "identity:\n  provider: ldap\n", "custom.yaml")
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(path))
    with pytest.raises(ValidationError):
        OrgBrainSettings()


# ── Helpers ──────────────────────────────────────────────────────────


def test_mcp_tool_joins_prefix_and_name() -> None:
    mcp = McpConfig()
    assert (
        mcp.tool("atlassian", "searchJiraIssuesUsingJql")
        == "mcp__atlassian__searchJiraIssuesUsingJql"
    )
    assert (
        mcp.tool("slack_write", "slack_send_message")
        == "mcp__plugin_slack_slack__slack_send_message"
    )


def test_mcp_tool_unknown_server_raises_config_error() -> None:
    with pytest.raises(ConfigError, match="figma"):
        McpConfig().tool("figma", "get_file")


def test_jira_browse_url() -> None:
    jira = JiraSourceConfig(base_url="https://acme.atlassian.net/")
    assert jira.browse_url("ABC-1") == "https://acme.atlassian.net/browse/ABC-1"


def test_jira_browse_url_none_without_base_url() -> None:
    assert JiraSourceConfig().browse_url("ABC-1") is None


def test_conventions_model_standalone() -> None:
    assert ConventionsConfig().slack_channel == "#{team}"


# ── Shipped config files ─────────────────────────────────────────────


def test_example_yaml_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(REPO_ROOT / "orgbrain.example.yaml"))
    s = OrgBrainSettings()
    assert s.mcp.tool_prefix == EXPECTED_MCP_PREFIXES
    assert s.manifest.providers == ["backstage", "codeowners"]


def test_acmeco_yaml_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORGBRAIN_CONFIG", str(REPO_ROOT / "examples" / "acmeco" / "orgbrain.yaml"))
    s = OrgBrainSettings()
    assert s.org.name == "acmeco"
    assert s.sources.github.orgs == ["acmeco"]
    assert s.sources.jira.base_url == "https://acmeco.atlassian.net"
    assert s.linking.internal_package_prefixes == ["com.acmeco.", "@acmeco/", "github.com/acmeco/"]
    assert s.conventions.placeholder_teams == []
