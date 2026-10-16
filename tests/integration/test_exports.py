"""Integration tests for JSON, CSV, and HTML export generation."""

import pytest
from httpx import AsyncClient

from opentrace.reports.csv_report import export_csv
from opentrace.reports.html_report import export_html
from opentrace.reports.json_report import export_json


@pytest.fixture
def sample_investigation():
    return {
        "id": "11111111-2222-3333-4444-555555555555",
        "created_at": "2026-10-16T12:00:00Z",
        "completed_at": "2026-10-16T12:00:05Z",
        "status": "completed",
        "request": {"username": "octocat"},
        "findings": [
            {
                "id": "find-1",
                "module_id": "username.github",
                "module_version": "0.1.0",
                "target_type": "username",
                "status": "found",
                "title": "=cmd|' /C calc'!A0",  # Test CSV injection payload
                "evidence": "<script>alert('xss')</script>",  # Test XSS payload
                "source_name": "GitHub",
                "source_url": "https://github.com/octocat",
                "observed_at": "2026-10-16T12:00:02Z",
                "confidence": "medium",
                "data": {"login": "octocat"},
                "evidence_hash": "a1b2c3d4e5f60718",
            }
        ],
        "entities": [
            {
                "id": "ent-1",
                "type": "platform",
                "value": "github",
                "display_label": "GitHub",
            }
        ],
        "edges": [],
        "warnings": ["Sample warning"],
        "summary": {"total": 1, "by_status": {"found": 1}},
    }


def test_json_export(sample_investigation):
    exported = export_json(sample_investigation)
    assert "11111111-2222-3333-4444-555555555555" in exported
    assert "octocat" in exported


def test_csv_export_injection_mitigation(sample_investigation):
    csv_text = export_csv(sample_investigation)
    # The cell starting with '=' must be sanitized with leading single-quote
    assert "'=cmd|" in csv_text
    assert "find-1" in csv_text


def test_html_export_xss_protection(sample_investigation):
    html_text = export_html(sample_investigation)
    # Untrusted XSS payload in evidence must be HTML escaped
    assert "<script>alert('xss')</script>" not in html_text
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_text
    assert "11111111-2222-3333-4444-555555555555" in html_text


@pytest.mark.asyncio
async def test_export_api_endpoints(async_client: AsyncClient, sample_investigation):
    # Save into storage first by creating an investigation or mocking
    # Let's create an investigation via API
    res = await async_client.post("/api/v1/investigations", json={"phone": "+12025550123"})
    inv_id = res.json()["id"]

    # Test JSON export
    res_json = await async_client.get(f"/api/v1/investigations/{inv_id}/export?format=json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]

    # Test CSV export
    res_csv = await async_client.get(f"/api/v1/investigations/{inv_id}/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    # Test HTML export
    res_html = await async_client.get(f"/api/v1/investigations/{inv_id}/export?format=html")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
