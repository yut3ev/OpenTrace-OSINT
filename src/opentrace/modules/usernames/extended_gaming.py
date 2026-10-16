"""Extended gaming, security, competitive programming, and media platform adapters."""

from __future__ import annotations

from typing import Any

from opentrace.api.schemas.common import TargetType
from opentrace.modules.base import BaseUsernameAdapter, ModuleMetadata


class SteamUsernameModule(BaseUsernameAdapter):
    """Verifies Steam Community public gamer profiles by custom vanity URL."""

    metadata = ModuleMetadata(
        id="username.steam",
        name="Steam Community",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Steam Community",
        source_url="https://steamcommunity.com/id/{username}",
        description="Public gamer profile, badges, and games library on Steam.",
        category="gaming",
        access_type="public_web",
        limitations=["Steam profiles set to Friends-Only hide badges and game lists"],
    )
    url_pattern = "https://steamcommunity.com/id/{username}"
    soft_404_indicators = ["The specified profile could not be found", "Error 502", "Error 404"]


class TwitchUsernameModule(BaseUsernameAdapter):
    """Verifies live streaming channel on Twitch."""

    metadata = ModuleMetadata(
        id="username.twitch",
        name="Twitch",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Twitch",
        source_url="https://www.twitch.tv/{username}",
        description="Live video streaming channel and broadcaster profile on Twitch.",
        category="gaming",
        access_type="public_web",
        limitations=["Banned or deactivated channels return content unavailable"],
    )
    url_pattern = "https://www.twitch.tv/{username}"
    soft_404_indicators = [
        "Time travel has not been invented",
        "Unless you've got a time machine, that content is unavailable",
        "404",
    ]


class GoodreadsUsernameModule(BaseUsernameAdapter):
    """Verifies book reader and author profiles on Goodreads."""

    metadata = ModuleMetadata(
        id="username.goodreads",
        name="Goodreads",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Goodreads",
        source_url="https://www.goodreads.com/{username}",
        description="Public reading list, reviews, and book author profile on Goodreads.",
        category="social",
        access_type="public_web",
        limitations=["Numeric user IDs are standard; vanity usernames are optional"],
    )
    url_pattern = "https://www.goodreads.com/{username}"
    soft_404_indicators = ["Page not found", "Page Unavailable", "404"]


class LetterboxdUsernameModule(BaseUsernameAdapter):
    """Verifies film enthusiast diary and review profiles on Letterboxd."""

    metadata = ModuleMetadata(
        id="username.letterboxd",
        name="Letterboxd",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Letterboxd",
        source_url="https://letterboxd.com/{username}/",
        description="Film diary, movie ratings, and reviews on Letterboxd.",
        category="social",
        access_type="public_web",
        limitations=["Private accounts mask film diary"],
    )
    url_pattern = "https://letterboxd.com/{username}/"
    soft_404_indicators = ["Page not found", "Sorry, we can’t find that page", "404"]


class LastFmUsernameModule(BaseUsernameAdapter):
    """Verifies music scrobble history and music taste profile on Last.fm."""

    metadata = ModuleMetadata(
        id="username.lastfm",
        name="Last.fm",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Last.fm",
        source_url="https://www.last.fm/user/{username}",
        description="Public music scrobbles, top tracks, and listening habits on Last.fm.",
        category="social",
        access_type="public_web",
        limitations=["Deleted accounts show standard user not found banner"],
    )
    url_pattern = "https://www.last.fm/user/{username}"
    soft_404_indicators = ["User not found", "Page Not Found", "404 - User not found"]


class StravaUsernameModule(BaseUsernameAdapter):
    """Verifies public athletic athlete profiles on Strava fitness network."""

    metadata = ModuleMetadata(
        id="username.strava",
        name="Strava",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Strava",
        source_url="https://www.strava.com/athletes/{username}",
        description="Athlete public profile, running/cycling activities on Strava.",
        category="social",
        access_type="public_web",
        limitations=["Requires custom athlete vanity username"],
    )
    url_pattern = "https://www.strava.com/athletes/{username}"
    soft_404_indicators = [
        "The page you were looking for doesn't exist",
        "Athlete Not Found",
        "404",
    ]


class DuolingoUsernameModule(BaseUsernameAdapter):
    """Verifies language learner profiles on Duolingo via public API."""

    metadata = ModuleMetadata(
        id="username.duolingo",
        name="Duolingo",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Duolingo",
        source_url="https://www.duolingo.com/profile/{username}",
        description="Language learning streak, learned languages, and XP on Duolingo.",
        category="social",
        access_type="public_api",
        limitations=["Private profiles hide streak and friend activity"],
    )
    url_pattern = "https://www.duolingo.com/2017-06-30/users?username={username}"
    profile_url_pattern = "https://www.duolingo.com/profile/{username}"
    is_json_api = True

    def extract_profile_data(self, response: Any, username: str) -> dict[str, Any]:
        try:
            data = response.json()
            users = data.get("users", [])
            if users:
                u = users[0]
                return {
                    "username": username,
                    "profile_url": self.get_profile_url(username),
                    "display_name": u.get("name") or username,
                    "streak": u.get("streak"),
                    "total_xp": u.get("totalXp"),
                    "courses": [c.get("title") for c in u.get("courses", [])],
                }
        except Exception:
            pass
        return super().extract_profile_data(response, username)


class TryHackMeUsernameModule(BaseUsernameAdapter):
    """Verifies cybersecurity learner and hacker rank profiles on TryHackMe."""

    metadata = ModuleMetadata(
        id="username.tryhackme",
        name="TryHackMe",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="TryHackMe",
        source_url="https://tryhackme.com/p/{username}",
        description="Cybersecurity skill rank, badges, and completed rooms on TryHackMe.",
        category="gaming",
        access_type="public_api",
        limitations=["Private rankings hide global position"],
    )
    url_pattern = "https://tryhackme.com/api/user/exist/{username}"
    profile_url_pattern = "https://tryhackme.com/p/{username}"
    is_json_api = True
    json_required_keys = ["success"]


class LeetCodeUsernameModule(BaseUsernameAdapter):
    """Verifies competitive programming and software engineering profiles on LeetCode."""

    metadata = ModuleMetadata(
        id="username.leetcode",
        name="LeetCode",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="LeetCode",
        source_url="https://leetcode.com/{username}/",
        description="Public problem solving stats, contest rating, and rank on LeetCode.",
        category="developer",
        access_type="public_web",
        limitations=["Contest rankings update periodically"],
    )
    url_pattern = "https://leetcode.com/{username}/"
    soft_404_indicators = [
        "Page not found",
        "User not found",
        "404 - Not Found",
        "page does not exist",
    ]


class CodeforcesUsernameModule(BaseUsernameAdapter):
    """Verifies competitive programmer ratings on Codeforces via official API."""

    metadata = ModuleMetadata(
        id="username.codeforces",
        name="Codeforces",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Codeforces",
        source_url="https://codeforces.com/profile/{username}",
        description="Competitive programming rating, rank, and contest participation on Codeforces.",
        category="developer",
        access_type="public_api",
        limitations=["Official API throttles to 1 request per 2 seconds per IP"],
    )
    url_pattern = "https://codeforces.com/api/user.info?handles={username}"
    profile_url_pattern = "https://codeforces.com/profile/{username}"
    is_json_api = True

    def extract_profile_data(self, response: Any, username: str) -> dict[str, Any]:
        try:
            data = response.json()
            if data.get("status") == "OK" and data.get("result"):
                u = data["result"][0]
                return {
                    "username": username,
                    "profile_url": self.get_profile_url(username),
                    "rating": u.get("rating"),
                    "rank": u.get("rank"),
                    "max_rating": u.get("maxRating"),
                    "max_rank": u.get("maxRank"),
                    "organization": u.get("organization"),
                }
        except Exception:
            pass
        return super().extract_profile_data(response, username)


class TelegramUsernameModule(BaseUsernameAdapter):
    """Verifies public channels and accounts on Telegram via t.me public preview."""

    metadata = ModuleMetadata(
        id="username.telegram",
        name="Telegram",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Telegram",
        source_url="https://t.me/{username}",
        description="Public Telegram handle, channel, or bot preview.",
        category="messaging",
        access_type="public_web",
        limitations=["Private personal accounts without public username do not resolve on t.me"],
    )
    url_pattern = "https://t.me/{username}"
    soft_404_indicators = [
        "If you have Telegram, you can contact",
        "tgme_page_extra",
        "If you have Telegram, you can view and join",
    ]

    def extract_profile_data(self, response: Any, username: str) -> dict[str, Any]:
        return {
            "username": username,
            "profile_url": self.get_profile_url(username),
            "channel": f"@{username}",
        }
