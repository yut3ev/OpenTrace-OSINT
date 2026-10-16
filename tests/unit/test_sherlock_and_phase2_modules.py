"""Unit tests for Phase 2 free OSINT modules, Sherlock adapters, and unified search contract."""

from __future__ import annotations

import pytest
import respx

from opentrace.api.schemas.common import FindingStatus, SourceStatus
from opentrace.modules.email.free_osint import (
    EmailCertificateTransparencyModule,
    EmailRDAPDomainModule,
    EmailSecurityTxtModule,
)
from opentrace.modules.people.free_people import (
    SemanticScholarAuthorModule,
    WikidataEntityModule,
    WikipediaFullTextSearchModule,
)
from opentrace.modules.phone.free_phone import (
    PhoneTimezoneModule,
    PhoneValidationRulesModule,
)
from opentrace.modules.registry import get_default_registry
from opentrace.modules.usernames.sherlock_community import (
    SpeedrunUsernameModule,
)
from opentrace.modules.usernames.sherlock_creative import (
    DeviantArtUsernameModule,
)
from opentrace.modules.usernames.sherlock_developer import (
    CodewarsUsernameModule,
    HackerRankUsernameModule,
)
from opentrace.modules.web.search import DuckDuckGoInstantModule, OpenWebSearchModule


@pytest.mark.asyncio
async def test_duckduckgo_instant_found():
    mod = DuckDuckGoInstantModule()
    with respx.mock:
        respx.get(
            "https://api.duckduckgo.com/?q=torvalds&format=json&no_html=1&skip_disambig=1"
        ).respond(
            200,
            json={
                "Heading": "Linus Torvalds",
                "Abstract": "Linus Benedict Torvalds is a Finnish-American software engineer who is the creator of Linux.",
                "AbstractURL": "https://en.wikipedia.org/wiki/Linus_Torvalds",
                "RelatedTopics": [],
            },
        )
        findings = await mod.run("torvalds")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert findings[0]["source_status"] == SourceStatus.succeeded.value
        assert "Linus Torvalds" in findings[0]["title"]


@pytest.mark.asyncio
async def test_duckduckgo_instant_not_found():
    mod = DuckDuckGoInstantModule()
    with respx.mock:
        respx.get(
            "https://api.duckduckgo.com/?q=nonexistent123xyz&format=json&no_html=1&skip_disambig=1"
        ).respond(200, json={"Heading": "", "Abstract": "", "AbstractURL": "", "RelatedTopics": []})
        findings = await mod.run("nonexistent123xyz")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.not_found.value
        assert findings[0]["source_status"] == SourceStatus.no_match.value


@pytest.mark.asyncio
async def test_open_web_search():
    mod = OpenWebSearchModule()
    with respx.mock:
        respx.get("https://html.duckduckgo.com/html/?q=testquery").respond(
            200, text="<html><body><div class='result__snippet'>Sample snippet</div></body></html>"
        )
        findings = await mod.run("testquery")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert "structured_queries" in findings[0]["data"]


@pytest.mark.asyncio
async def test_email_rdap_domain_found():
    mod = EmailRDAPDomainModule()
    with respx.mock:
        respx.get("https://rdap.org/domain/example.com").respond(
            200,
            json={
                "handle": "EXAMPLE-DOM",
                "status": ["active", "clientDeleteProhibited"],
                "events": [{"eventAction": "registration", "eventDate": "1995-08-14T04:00:00Z"}],
            },
        )
        findings = await mod.run("admin@example.com")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert findings[0]["data"]["handle"] == "EXAMPLE-DOM"


@pytest.mark.asyncio
async def test_email_security_txt_found():
    mod = EmailSecurityTxtModule()
    with respx.mock:
        respx.get("https://example.com/.well-known/security.txt").respond(
            200,
            text="Contact: mailto:security@example.com\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en",
        )
        findings = await mod.run("user@example.com")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert "mailto:security@example.com" in findings[0]["data"]["contacts"]


@pytest.mark.asyncio
async def test_email_cert_transparency_found():
    mod = EmailCertificateTransparencyModule()
    with respx.mock:
        respx.get("https://crt.sh/?q=%25.example.com&output=json").respond(
            200,
            json=[
                {"name_value": "example.com\napi.example.com"},
                {"name_value": "mail.example.com"},
            ],
        )
        findings = await mod.run("user@example.com")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert findings[0]["data"]["total_certificates"] == 2
        assert "api.example.com" in findings[0]["data"]["discovered_subdomains"]


@pytest.mark.asyncio
async def test_phone_timezone_module():
    mod = PhoneTimezoneModule()
    # US number (+1 415 555 2671)
    findings = await mod.run("+14155552671")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "America/Los_Angeles" in findings[0]["data"]["applicable_timezones"]


@pytest.mark.asyncio
async def test_phone_validation_rules_module():
    mod = PhoneValidationRulesModule()
    # Valid UK mobile (+44 7911 123456)
    findings = await mod.run("+447911123456")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["is_valid"] is True
    assert findings[0]["data"]["line_type"] == "mobile"


@pytest.mark.asyncio
async def test_wikidata_entity_found():
    mod = WikidataEntityModule()
    with respx.mock:
        respx.get(
            "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Ada+Lovelace&language=en&format=json"
        ).respond(
            200,
            json={
                "search": [
                    {
                        "id": "Q7259",
                        "label": "Ada Lovelace",
                        "description": "English mathematician and first computer programmer",
                        "concepturi": "http://www.wikidata.org/entity/Q7259",
                    }
                ]
            },
        )
        findings = await mod.run("Ada Lovelace")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert findings[0]["data"]["qid"] == "Q7259"


@pytest.mark.asyncio
async def test_semantic_scholar_author_found():
    mod = SemanticScholarAuthorModule()
    with respx.mock:
        respx.get(
            "https://api.semanticscholar.org/graph/v1/author/search?query=Claude+Shannon&fields=name,aliases,affiliations,paperCount,citationCount,hIndex&limit=3"
        ).respond(
            200,
            json={
                "data": [
                    {
                        "authorId": "1741101",
                        "name": "Claude E. Shannon",
                        "paperCount": 128,
                        "citationCount": 115000,
                        "hIndex": 45,
                        "affiliations": ["Bell Labs", "MIT"],
                    }
                ]
            },
        )
        findings = await mod.run("Claude Shannon")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert findings[0]["data"]["h_index"] == 45


@pytest.mark.asyncio
async def test_wikipedia_full_text_search():
    mod = WikipediaFullTextSearchModule()
    with respx.mock:
        respx.get(
            "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Alan+Turing&format=json&srlimit=3"
        ).respond(
            200,
            json={
                "query": {
                    "search": [
                        {
                            "title": "Alan Turing",
                            "snippet": "Alan Mathison Turing was an English mathematician, computer scientist...",
                            "wordcount": 14200,
                        }
                    ]
                }
            },
        )
        findings = await mod.run("Alan Turing")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert "Alan Turing" in findings[0]["data"]["title"]


@pytest.mark.asyncio
async def test_sherlock_hackerrank_found():
    mod = HackerRankUsernameModule()
    with respx.mock:
        respx.get("https://www.hackerrank.com/rest/hackers/alice").respond(
            200, json={"model": {"username": "alice", "name": "Alice Developer"}}
        )
        findings = await mod.run("alice")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value
        assert findings[0]["source_status"] == SourceStatus.succeeded.value


@pytest.mark.asyncio
async def test_sherlock_codewars_found():
    mod = CodewarsUsernameModule()
    with respx.mock:
        respx.get("https://www.codewars.com/api/v1/users/codewarrior").respond(
            200, json={"username": "codewarrior", "honor": 1250}
        )
        findings = await mod.run("codewarrior")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
async def test_sherlock_deviantart_soft_404():
    mod = DeviantArtUsernameModule()
    with respx.mock:
        respx.get("https://www.deviantart.com/unknownartist").respond(
            200, text="<html><body><h1>404 Not Found</h1><p>Deactivated Account</p></body></html>"
        )
        findings = await mod.run("unknownartist")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.not_found.value
        assert findings[0]["source_status"] == SourceStatus.no_match.value


@pytest.mark.asyncio
async def test_sherlock_speedrun_found():
    mod = SpeedrunUsernameModule()
    with respx.mock:
        respx.get("https://www.speedrun.com/api/v1/users/fastrunner").respond(
            200, json={"data": {"id": "123", "names": {"international": "fastrunner"}}}
        )
        findings = await mod.run("fastrunner")
        assert len(findings) == 1
        assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
async def test_adapter_contract_section_7():
    """Verify Section 7 contract attributes and methods across all registered modules."""
    registry = get_default_registry()
    all_modules = registry.list_all()

    # Must have between 100 and 250 modules
    assert 100 <= len(all_modules) <= 250

    for mod in all_modules:
        # Check required properties
        assert mod.source_id == mod.metadata.id
        assert mod.source_name == mod.metadata.source_name
        assert mod.category == mod.metadata.category
        assert mod.base_url == mod.metadata.source_url
        assert isinstance(mod.is_free, bool)
        assert isinstance(mod.requires_api_key, bool)
        assert isinstance(mod.timeout, float)
        assert isinstance(mod.rate_limit_policy, str)

        # Check required methods
        assert await mod.check_availability() is True
        health = await mod.health_check()
        assert health["status"] == "healthy"
        assert health["source_id"] == mod.source_id
