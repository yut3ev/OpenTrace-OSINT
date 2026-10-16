"""Unit tests for Typer and Rich CLI commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from opentrace.api.schemas.investigation import InvestigationResponse, SummarySchema
from opentrace.cli.main import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "OpenTrace OSINT" in result.stdout


def test_cli_modules_table():
    result = runner.invoke(app, ["modules"])
    assert result.exit_code == 0
    assert "username.github" in result.stdout
    assert "email.syntax" in result.stdout
    assert "phone.numbering" in result.stdout


def test_cli_modules_json():
    result = runner.invoke(app, ["modules", "--json"])
    assert result.exit_code == 0
    assert '"id": "username.github"' in result.stdout


def test_cli_investigate_missing_args():
    result = runner.invoke(app, ["investigate"])
    # Should exit with code 2 when no target specified
    assert result.exit_code == 2


def test_cli_investigate_success():
    fake_response = InvestigationResponse(
        id="test-cli-1234",
        status="completed",  # type: ignore[arg-type]
        created_at="2026-10-16T12:00:00Z",  # type: ignore[arg-type]
        request={"username": "octocat"},
        findings=[],
        entities=[],
        edges=[],
        summary=SummarySchema(total=0, by_status={}, duration_seconds=0.1),
        warnings=[],
    )

    with patch(
        "opentrace.core.orchestrator.InvestigationOrchestrator.run_investigation",
        return_value=fake_response,
    ):
        result = runner.invoke(app, ["investigate", "--username", "octocat"])
        assert result.exit_code == 0
        assert "test-cli-1234" in result.stdout


def test_cli_investigate_json():
    fake_response = InvestigationResponse(
        id="test-cli-json",
        status="completed",  # type: ignore[arg-type]
        created_at="2026-10-16T12:00:00Z",  # type: ignore[arg-type]
        request={"phone": "+12025550123"},
        findings=[],
        entities=[],
        edges=[],
        summary=SummarySchema(total=0, by_status={}, duration_seconds=0.1),
        warnings=[],
    )

    with patch(
        "opentrace.core.orchestrator.InvestigationOrchestrator.run_investigation",
        return_value=fake_response,
    ):
        result = runner.invoke(app, ["investigate", "--phone", "+12025550123", "--json"])
        assert result.exit_code == 0
        assert '"id": "test-cli-json"' in result.stdout
