"""Conservative cross-source correlation.

All links are evidence-backed candidates unless explicit confirmation exists.
Similar usernames, display names, or avatars alone are weak signals and do NOT
create confirmed identity links.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """A typed entity extracted from findings."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: str = ""  # username, email, phone, domain, platform, profile_url
    value: str = ""
    display_label: str = ""


@dataclass
class Edge:
    """An evidence-backed candidate relationship between entities."""

    source_entity_id: str = ""
    dest_entity_id: str = ""
    relation: str = ""
    basis: str = ""
    confidence: str = "none"  # none, low, medium, high
    evidence_ids: list[str] = field(default_factory=list)
    label: str = "candidate"  # candidate or confirmed


def extract_entities(findings: list[dict[str, Any]]) -> list[Entity]:
    """Extract typed entities from findings.

    Creates entities for usernames, emails, phones, domains, and platforms
    observed in the findings.
    """
    entities: list[Entity] = []
    seen_values: set[str] = set()

    for finding in findings:
        target_type = finding.get("target_type", "")
        data = finding.get("data", {})
        module_id = finding.get("module_id", "")

        # Extract target as entity
        target_key = f"{target_type}:{finding.get('source_name', '')}"
        if target_key not in seen_values:
            seen_values.add(target_key)

        # Extract platform entity from module (e.g. username.github -> github)
        if "." in module_id:
            platform = module_id.split(".", 1)[1]
            platform_key = f"platform:{platform}"
            if platform_key not in seen_values:
                seen_values.add(platform_key)
                entities.append(
                    Entity(
                        type="platform",
                        value=platform,
                        display_label=platform.title(),
                    )
                )

        # Extract source URL as profile entity if found
        source_url = finding.get("source_url", "")
        if source_url and finding.get("status") == "found":
            url_key = f"profile_url:{source_url}"
            if url_key not in seen_values:
                seen_values.add(url_key)
                entities.append(
                    Entity(
                        type="profile_url",
                        value=source_url,
                        display_label=source_url,
                    )
                )

        # Extract domain from email findings
        if target_type == "email" and data.get("domain"):
            domain = data["domain"]
            domain_key = f"domain:{domain}"
            if domain_key not in seen_values:
                seen_values.add(domain_key)
                entities.append(
                    Entity(
                        type="domain",
                        value=domain,
                        display_label=domain,
                    )
                )

    return entities


def build_edges(entities: list[Entity], findings: list[dict[str, Any]]) -> list[Edge]:
    """Build conservative evidence-backed edges between entities.

    Only creates edges when explicit evidence supports the relationship.
    All edges are labeled 'candidate' since module findings alone cannot
    confirm that multiple accounts belong to the same person.
    """
    edges: list[Edge] = []

    # Group profile_url entities with their platform entities
    profile_entities = [e for e in entities if e.type == "profile_url"]
    platform_entities = {e.value: e for e in entities if e.type == "platform"}

    for profile in profile_entities:
        for platform_name, platform_entity in platform_entities.items():
            if platform_name in profile.value.lower():
                finding_ids = [
                    f.get("id", "") for f in findings if f.get("source_url") == profile.value
                ]
                edges.append(
                    Edge(
                        source_entity_id=profile.id,
                        dest_entity_id=platform_entity.id,
                        relation="hosted_on",
                        basis=f"Profile URL {profile.value} is on {platform_name}",
                        confidence="medium",
                        evidence_ids=finding_ids,
                        label="candidate",
                    )
                )

    return edges
