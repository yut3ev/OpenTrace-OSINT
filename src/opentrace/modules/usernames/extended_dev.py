"""Extended developer platform adapters: Codeberg, Hashnode, Kaggle, Replit, SourceForge, Packagist, RubyGems, Crates.io, StackExchange."""

from __future__ import annotations

from typing import Any

from opentrace.api.schemas.common import TargetType
from opentrace.modules.base import BaseUsernameAdapter, ModuleMetadata


class CodebergUsernameModule(BaseUsernameAdapter):
    """Verifies public profiles on Codeberg (Gitea-based open-source forge)."""

    metadata = ModuleMetadata(
        id="username.codeberg",
        name="Codeberg",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Codeberg",
        source_url="https://codeberg.org/{username}",
        description="Public developer profile and repositories on Codeberg open forge.",
        category="developer",
        access_type="public_api",
        limitations=["Unauthenticated rate limits apply"],
    )
    url_pattern = "https://codeberg.org/api/v1/users/{username}"
    profile_url_pattern = "https://codeberg.org/{username}"
    is_json_api = True
    json_required_keys = ["id", "username"]


class HashnodeUsernameModule(BaseUsernameAdapter):
    """Verifies public technical blogging profiles on Hashnode."""

    metadata = ModuleMetadata(
        id="username.hashnode",
        name="Hashnode",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Hashnode",
        source_url="https://hashnode.com/@{username}",
        description="Technical blogging and developer publication profile on Hashnode.",
        category="developer",
        access_type="public_web",
        limitations=["Custom domains may mask direct profile links"],
    )
    url_pattern = "https://hashnode.com/@{username}"
    soft_404_indicators = ["User not found", "This page could not be found", "404 - Page not found"]


class KaggleUsernameModule(BaseUsernameAdapter):
    """Verifies data science and machine learning practitioner profiles on Kaggle."""

    metadata = ModuleMetadata(
        id="username.kaggle",
        name="Kaggle",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Kaggle",
        source_url="https://www.kaggle.com/{username}",
        description="Public Kaggle profile, competitions rank, and datasets.",
        category="developer",
        access_type="public_web",
        limitations=["Profile privacy settings can limit public visibility"],
    )
    url_pattern = "https://www.kaggle.com/{username}"
    soft_404_indicators = ["We couldn't find that page", "User not found", "404"]


class ReplitUsernameModule(BaseUsernameAdapter):
    """Verifies public developer coding profiles on Replit."""

    metadata = ModuleMetadata(
        id="username.replit",
        name="Replit",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Replit",
        source_url="https://replit.com/@{username}",
        description="Public Replit software developer profile and repls.",
        category="developer",
        access_type="public_web",
        limitations=["Private repls are hidden"],
    )
    url_pattern = "https://replit.com/@{username}"
    soft_404_indicators = ["Not Found", "User does not exist", "404"]


class SourceForgeUsernameModule(BaseUsernameAdapter):
    """Verifies open-source developer project maintainers on SourceForge."""

    metadata = ModuleMetadata(
        id="username.sourceforge",
        name="SourceForge",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="SourceForge",
        source_url="https://sourceforge.net/u/{username}/profile/",
        description="SourceForge open-source developer profile and maintained projects.",
        category="developer",
        access_type="public_web",
        limitations=["Legacy account pages may contain minimal information"],
    )
    url_pattern = "https://sourceforge.net/u/{username}/profile/"
    soft_404_indicators = ["Page Not Found", "User not found", "No user found"]


class PackagistUsernameModule(BaseUsernameAdapter):
    """Verifies PHP package authors and vendors on Packagist / Composer."""

    metadata = ModuleMetadata(
        id="username.packagist",
        name="Packagist",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Packagist",
        source_url="https://packagist.org/packages/list.json?vendor={username}",
        description="PHP Composer package author and vendor registry entry.",
        category="developer",
        access_type="public_api",
        limitations=["Only indexes users who published public PHP packages"],
    )
    url_pattern = "https://packagist.org/packages/list.json?vendor={username}"
    profile_url_pattern = "https://packagist.org/packages/{username}/"
    is_json_api = True

    def extract_profile_data(self, response: Any, username: str) -> dict[str, Any]:
        try:
            data = response.json()
            package_names = data.get("packageNames", [])
            return {
                "username": username,
                "profile_url": self.get_profile_url(username),
                "packages": package_names,
                "package_count": len(package_names),
            }
        except Exception:
            return super().extract_profile_data(response, username)


class RubyGemsUsernameModule(BaseUsernameAdapter):
    """Verifies Ruby gem authors on RubyGems package registry."""

    metadata = ModuleMetadata(
        id="username.rubygems",
        name="RubyGems",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="RubyGems",
        source_url="https://rubygems.org/profiles/{username}",
        description="Ruby gems author profile and published packages.",
        category="developer",
        access_type="public_api",
        limitations=["Returns 404 if user has published no public gems"],
    )
    url_pattern = "https://rubygems.org/api/v1/owners/{username}/gems.json"
    profile_url_pattern = "https://rubygems.org/profiles/{username}"
    is_json_api = True


class CratesIoUsernameModule(BaseUsernameAdapter):
    """Verifies Rust package authors on Crates.io package registry."""

    metadata = ModuleMetadata(
        id="username.cratesio",
        name="Crates.io",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Crates.io",
        source_url="https://crates.io/users/{username}",
        description="Rust crates author profile and published crates on Crates.io.",
        category="developer",
        access_type="public_api",
        limitations=["Strict user-agent header required by crates.io terms"],
    )
    url_pattern = "https://crates.io/api/v1/users/{username}"
    profile_url_pattern = "https://crates.io/users/{username}"
    is_json_api = True
    custom_headers = {"User-Agent": "OpenTrace-OSINT/1.0 (research; contact@opentrace-osint.local)"}
    json_required_keys = ["user"]


class StackExchangeUsernameModule(BaseUsernameAdapter):
    """Searches Stack Overflow / Stack Exchange network public developer profiles."""

    metadata = ModuleMetadata(
        id="username.stackexchange",
        name="Stack Overflow",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Stack Overflow",
        source_url="https://stackoverflow.com/users",
        description="Public developer reputation, answers, and profile on Stack Overflow network.",
        category="developer",
        access_type="public_api",
        limitations=["Stack Exchange API throttle applies to unauthenticated requests"],
    )
    url_pattern = "https://api.stackexchange.com/2.3/users?inname={username}&site=stackoverflow"
    profile_url_pattern = "https://stackoverflow.com/users"
    is_json_api = True

    def extract_profile_data(self, response: Any, username: str) -> dict[str, Any]:
        try:
            data = response.json()
            items = data.get("items", [])
            for item in items:
                if item.get("display_name", "").lower() == username.lower():
                    return {
                        "username": username,
                        "display_name": item.get("display_name"),
                        "reputation": item.get("reputation"),
                        "profile_url": item.get("link"),
                        "avatar_url": item.get("profile_image"),
                        "location": item.get("location"),
                    }
        except Exception:
            pass
        return super().extract_profile_data(response, username)
