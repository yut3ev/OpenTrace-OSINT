"""Unit tests for evidence tracking and hashing."""

from dataclasses import FrozenInstanceError

import pytest

from opentrace.core.evidence import EvidenceRecord, compute_evidence_hash


def test_compute_evidence_hash_deterministic():
    h1 = compute_evidence_hash("https://example.com", 200, "found")
    h2 = compute_evidence_hash("https://example.com", 200, "found")
    assert h1 == h2
    assert len(h1) == 16


def test_compute_evidence_hash_changes_with_input():
    h1 = compute_evidence_hash("https://example.com", 200, "found")
    h2 = compute_evidence_hash("https://example.com", 404, "not_found")
    assert h1 != h2


def test_evidence_record_auto_computes_hash():
    rec = EvidenceRecord(
        module_id="username.github",
        source_name="GitHub",
        source_url="https://api.github.com/users/octocat",
        raw_status_code=200,
        response_summary="profile found",
    )
    assert rec.evidence_hash != ""
    assert len(rec.evidence_hash) == 16


def test_evidence_record_immutability():
    rec = EvidenceRecord(
        module_id="username.github",
        source_name="GitHub",
        source_url="https://api.github.com/users/octocat",
    )
    with pytest.raises(FrozenInstanceError):
        rec.module_id = "other"  # type: ignore[misc]
