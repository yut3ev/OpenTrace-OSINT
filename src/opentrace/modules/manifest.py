"""Source manifest loader and repository catalog."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger("opentrace.modules.manifest")


@dataclass
class ManifestSource:
    """A source specification from the source manifest."""

    id: str
    name: str
    category: str
    target_type: str
    access_type: str
    source_url: str
    status: str  # implemented, tested, requires_api_key, planned, temporarily_unavailable
    capabilities: list[str] = field(default_factory=list)
    description: str = ""
    limitations: list[str] = field(default_factory=list)
    api_url: str | None = None


_cached_manifest: list[ManifestSource] | None = None


def find_manifest_path() -> Path | None:
    """Locate sources/manifest.yaml relative to package or current working directory."""
    candidates = [
        Path("sources/manifest.yaml"),
        Path(__file__).resolve().parent.parent.parent.parent / "sources" / "manifest.yaml",
        Path.cwd() / "sources" / "manifest.yaml",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_manifest() -> list[ManifestSource]:
    """Load and parse the sources/manifest.yaml file."""
    global _cached_manifest
    if _cached_manifest is not None:
        return _cached_manifest

    path = find_manifest_path()
    if not path:
        logger.warning("sources/manifest.yaml not found, returning empty manifest.")
        return []

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        sources_raw = data.get("sources", [])
        manifest = []
        for s in sources_raw:
            manifest.append(
                ManifestSource(
                    id=s.get("id", ""),
                    name=s.get("name", ""),
                    category=s.get("category", "general"),
                    target_type=s.get("target_type", "username"),
                    access_type=s.get("access_type", "public_web"),
                    source_url=s.get("source_url", ""),
                    status=s.get("status", "planned"),
                    capabilities=s.get("capabilities", []),
                    description=s.get("description", ""),
                    limitations=s.get("limitations", []),
                    api_url=s.get("api_url"),
                )
            )
        _cached_manifest = manifest
        return manifest
    except Exception as exc:
        logger.error("Failed to load sources/manifest.yaml: %s", exc)
        return []


def get_source_manifest_entry(source_id: str) -> ManifestSource | None:
    """Find a specific source in the manifest by its ID."""
    for s in load_manifest():
        if s.id == source_id:
            return s
    return None
