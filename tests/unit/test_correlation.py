"""Unit tests for entity extraction, edge correlation, and deduplication."""

from opentrace.core.correlation import build_edges, extract_entities
from opentrace.core.deduplication import deduplicate_findings


def test_extract_entities_from_findings():
    findings = [
        {
            "id": "f1",
            "module_id": "username.github",
            "target_type": "username",
            "status": "found",
            "source_name": "GitHub",
            "source_url": "https://github.com/octocat",
            "data": {"login": "octocat"},
        },
        {
            "id": "f2",
            "module_id": "email.dns",
            "target_type": "email",
            "status": "info",
            "source_name": "DNS",
            "source_url": "dns://example.com/MX",
            "data": {"domain": "example.com"},
        },
    ]

    entities = extract_entities(findings)
    types = {e.type for e in entities}
    assert "platform" in types
    assert "profile_url" in types
    assert "domain" in types


def test_build_edges_conservative():
    findings = [
        {
            "id": "f1",
            "module_id": "username.github",
            "target_type": "username",
            "status": "found",
            "source_url": "https://github.com/octocat",
        }
    ]
    entities = extract_entities(findings)
    edges = build_edges(entities, findings)

    # Edge between profile_url and github platform
    assert len(edges) >= 1
    edge = edges[0]
    assert edge.relation == "hosted_on"
    assert edge.label == "candidate"  # Must remain candidate
    assert "f1" in edge.evidence_ids


def test_deduplicate_findings_preserves_provenance():
    findings = [
        {
            "module_id": "username.github",
            "target_type": "username",
            "status": "found",
            "source_url": "https://github.com/octocat",
            "evidence": "Evidence A",
        },
        {
            "module_id": "username.github",
            "target_type": "username",
            "status": "found",
            "source_url": "https://github.com/octocat",
            "evidence": "Evidence B",
        },
    ]

    deduped = deduplicate_findings(findings)
    assert len(deduped) == 1
    # Evidence merged, not lost
    assert "Evidence A" in deduped[0]["evidence"]
    assert "Evidence B" in deduped[0]["evidence"]
