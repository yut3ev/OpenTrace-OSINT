"""Integration tests for the investigation orchestrator."""

from unittest.mock import MagicMock, patch

import dns.resolver
import pytest
import respx
from httpx import Response

from opentrace.api.schemas.investigation import InvestigationRequest
from opentrace.core.orchestrator import InvestigationOrchestrator
from opentrace.storage.memory import MemoryStorage


@pytest.mark.asyncio
@respx.mock
async def test_orchestrator_multi_target_investigation():
    # Mock GitHub
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=Response(
            200,
            json={
                "login": "octocat",
                "name": "The Octocat",
                "html_url": "https://github.com/octocat",
            },
        )
    )
    # Mock GitLab
    respx.get("https://gitlab.com/api/v4/users?username=octocat").mock(
        return_value=Response(200, json=[])
    )

    # Mock DNS
    mock_mx = MagicMock()
    mock_mx.preference = 10
    mock_mx.exchange = "mail.example.com."

    storage = MemoryStorage()
    orchestrator = InvestigationOrchestrator(storage=storage)

    req = InvestigationRequest(
        username="octocat",
        email="dev@example.com",
        phone="+12025550123",
    )

    with patch.object(dns.resolver.Resolver, "resolve", return_value=[mock_mx]):
        result = await orchestrator.run_investigation(req)

    assert result.id is not None
    assert result.status.value in ("completed", "partial")
    assert len(result.findings) >= 4  # GitHub, GitLab, Email syntax, Email DNS, Phone numbering
    assert len(result.entities) > 0

    # Ensure saved in storage
    saved = await storage.get_investigation(result.id)
    assert saved is not None
    assert saved["id"] == result.id


@pytest.mark.asyncio
async def test_orchestrator_invalid_target_handling():
    storage = MemoryStorage()
    orchestrator = InvestigationOrchestrator(storage=storage)

    req = InvestigationRequest(
        username="invalid user with spaces!",
    )

    result = await orchestrator.run_investigation(req)
    assert result.status.value == "failed"
    assert len(result.warnings) > 0
