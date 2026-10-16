"""Sherlock-adapted developer and technical platform adapters (MIT Licensed)."""

from __future__ import annotations

from opentrace.api.schemas.common import TargetType
from opentrace.modules.base import BaseUsernameAdapter, ModuleMetadata


class HackerRankUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.hackerrank",
        name="HackerRank",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="HackerRank",
        source_url="https://www.hackerrank.com/{username}",
        description="Competitive programming and coding challenges profile on HackerRank.",
        category="developer",
        access_type="public_api",
        limitations=["Public profile badges and score."],
        license="MIT",
    )
    url_pattern = "https://www.hackerrank.com/rest/hackers/{username}"
    profile_url_pattern = "https://www.hackerrank.com/{username}"
    is_json_api = True
    json_required_keys = ["model"]


class CodewarsUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.codewars",
        name="Codewars",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Codewars",
        source_url="https://www.codewars.com/users/{username}",
        description="Coding challenge warrior profile, honor score, and completed kata.",
        category="developer",
        access_type="public_api",
        limitations=["Public ranking and honor only."],
        license="MIT",
    )
    url_pattern = "https://www.codewars.com/api/v1/users/{username}"
    profile_url_pattern = "https://www.codewars.com/users/{username}"
    is_json_api = True
    json_required_keys = ["username"]


class CodecademyUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.codecademy",
        name="Codecademy",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Codecademy",
        source_url="https://www.codecademy.com/profiles/{username}",
        description="Interactive coding learning curriculum profile and badges.",
        category="developer",
        access_type="public_web",
        limitations=["Only public profiles visible."],
        license="MIT",
    )
    url_pattern = "https://www.codecademy.com/profiles/{username}"
    soft_404_indicators = ["Page Not Found", "Couldn't find that page", "Profile Not Found"]


class GeeksforGeeksUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.geeksforgeeks",
        name="GeeksforGeeks",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="GeeksforGeeks",
        source_url="https://www.geeksforgeeks.org/user/{username}/",
        description="Computer science articles author and problem solving ranking.",
        category="developer",
        access_type="public_web",
        limitations=["Public profile info only."],
        license="MIT",
    )
    url_pattern = "https://www.geeksforgeeks.org/user/{username}/"
    soft_404_indicators = ["User not found", "Page Not Found", "404 - Not Found"]


class TopcoderUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.topcoder",
        name="Topcoder",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Topcoder",
        source_url="https://www.topcoder.com/members/{username}",
        description="Competitive programming algorithm matches and design challenges.",
        category="developer",
        access_type="public_api",
        limitations=["Unauthenticated rating details."],
        license="MIT",
    )
    url_pattern = "https://api.topcoder.com/v5/members/{username}"
    profile_url_pattern = "https://www.topcoder.com/members/{username}"
    is_json_api = True
    json_required_keys = ["handle"]


class WakatimeUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.wakatime",
        name="WakaTime",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="WakaTime",
        source_url="https://wakatime.com/@{username}",
        description="Developer programming metrics, language breakdown, and coding time.",
        category="developer",
        access_type="public_web",
        limitations=["Only publicly shared leaderboards and profiles visible."],
        license="MIT",
    )
    url_pattern = "https://wakatime.com/@{username}"
    soft_404_indicators = ["Page Not Found", "wakatime-404", "This user is private"]


class HackTheBoxUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.hackthebox",
        name="Hack The Box",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Hack The Box",
        source_url="https://www.hackthebox.com/home/users/profile/{username}",
        description="Penetration testing and ethical hacking public profile.",
        category="developer",
        access_type="public_web",
        limitations=["Public profile cards."],
        license="MIT",
    )
    url_pattern = "https://www.hackthebox.com/home/users/profile/{username}"
    soft_404_indicators = ["404 Not Found", "Page Not Found", "User not found"]


class BugcrowdUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.bugcrowd",
        name="Bugcrowd",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Bugcrowd",
        source_url="https://bugcrowd.com/{username}",
        description="Crowdsourced bug bounty researcher profile, points, and hall of fame.",
        category="developer",
        access_type="public_web",
        limitations=["Public researcher rank."],
        license="MIT",
    )
    url_pattern = "https://bugcrowd.com/{username}"
    soft_404_indicators = ["We couldn't find that page", "404 Not Found", "Page Not Found"]


class LaunchpadUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.launchpad",
        name="Launchpad",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Launchpad (Ubuntu/Canonical)",
        source_url="https://launchpad.net/~{username}",
        description="Ubuntu packaging, Canonical open-source bug reports, and PPA repositories.",
        category="developer",
        access_type="public_web",
        limitations=["Public Launchpad user profile."],
        license="MIT",
    )
    url_pattern = "https://launchpad.net/~{username}"
    soft_404_indicators = ["does not exist in Launchpad", "Page Not Found"]


class AsciinemaUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.asciinema",
        name="asciinema",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="asciinema",
        source_url="https://asciinema.org/~{username}",
        description="Terminal session recordings and command line screencasts.",
        category="developer",
        access_type="public_web",
        limitations=["Public cast recordings."],
        license="MIT",
    )
    url_pattern = "https://asciinema.org/~{username}"


class AnkiWebUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.ankiweb",
        name="AnkiWeb",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="AnkiWeb",
        source_url="https://ankiweb.net/shared/byauthor/{username}",
        description="Spaced repetition flashcard shared deck author.",
        category="developer",
        access_type="public_web",
        limitations=["Shared deck author index."],
        license="MIT",
    )
    url_pattern = "https://ankiweb.net/shared/byauthor/{username}"
    soft_404_indicators = ["No shared decks found", "Invalid user"]


class FreeCodeCampUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.freecodecamp",
        name="freeCodeCamp",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="freeCodeCamp",
        source_url="https://www.freecodecamp.org/{username}",
        description="FreeCodeCamp curriculum certifications, streak, and completed tasks.",
        category="developer",
        access_type="public_web",
        limitations=["Public profile badges."],
        license="MIT",
    )
    url_pattern = "https://www.freecodecamp.org/{username}"
    soft_404_indicators = ["We can't find that page", "page-not-found", "404 Not Found"]


class CoderwallUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.coderwall",
        name="Coderwall",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Coderwall",
        source_url="https://coderwall.com/{username}",
        description="Developer achievement badges, pro-tips, and programming languages.",
        category="developer",
        access_type="public_web",
        limitations=["Public coderwall achievements."],
        license="MIT",
    )
    url_pattern = "https://coderwall.com/{username}"
    soft_404_indicators = ["404 - Not Found", "Page Not Found", "Coder not found"]


class LobstersUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.lobsters",
        name="Lobsters",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Lobsters",
        source_url="https://lobste.rs/u/{username}",
        description="Computing focused community stories and comments karma.",
        category="developer",
        access_type="public_web",
        limitations=["Public profile and invited-by tree."],
        license="MIT",
    )
    url_pattern = "https://lobste.rs/u/{username}"


class ScratchUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.scratch",
        name="MIT Scratch",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="MIT Scratch",
        source_url="https://scratch.mit.edu/users/{username}",
        description="MIT Scratch visual programming creator profile and shared projects.",
        category="developer",
        access_type="public_api",
        limitations=["Public project catalog."],
        license="MIT",
    )
    url_pattern = "https://api.scratch.mit.edu/users/{username}"
    profile_url_pattern = "https://scratch.mit.edu/users/{username}"
    is_json_api = True
    json_required_keys = ["username"]


class ExercismUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.exercism",
        name="Exercism",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Exercism",
        source_url="https://exercism.org/profiles/{username}",
        description="Code mentoring, learning tracks, and solutions on Exercism.",
        category="developer",
        access_type="public_web",
        limitations=["Public profile and badges."],
        license="MIT",
    )
    url_pattern = "https://exercism.org/profiles/{username}"


class WeblateUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.weblate",
        name="Weblate",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Weblate Hosted",
        source_url="https://hosted.weblate.org/user/{username}/",
        description="Continuous localization and translation contributor on Weblate.",
        category="developer",
        access_type="public_web",
        limitations=["Public translation contributions."],
        license="MIT",
    )
    url_pattern = "https://hosted.weblate.org/user/{username}/"


class GiteaUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.gitea",
        name="Gitea.com",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Gitea Cloud",
        source_url="https://gitea.com/{username}",
        description="Gitea cloud developer profile and public repositories.",
        category="developer",
        access_type="public_web",
        limitations=["Public repositories."],
        license="MIT",
    )
    url_pattern = "https://gitea.com/{username}"


class SourceHutUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.sourcehut",
        name="SourceHut",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="SourceHut (~sr.ht)",
        source_url="https://sr.ht/~{username}",
        description="Open-source software forge and mailing lists profile.",
        category="developer",
        access_type="public_web",
        limitations=["Public git/hg repositories."],
        license="MIT",
    )
    url_pattern = "https://sr.ht/~{username}"


class PastebinUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.pastebin",
        name="Pastebin",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Pastebin",
        source_url="https://pastebin.com/u/{username}",
        description="Public text and code paste author profile.",
        category="developer",
        access_type="public_web",
        limitations=["Public unlisted pastes."],
        license="MIT",
    )
    url_pattern = "https://pastebin.com/u/{username}"
    soft_404_indicators = ["Not Found", "Unknown User", "Page Not Found"]
