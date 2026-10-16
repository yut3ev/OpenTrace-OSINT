"""Sherlock-adapted community, forum, lifestyle, and gaming platform adapters (MIT Licensed)."""

from __future__ import annotations

from opentrace.api.schemas.common import TargetType
from opentrace.modules.base import BaseUsernameAdapter, ModuleMetadata


class QuoraUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.quora",
        name="Quora",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Quora",
        source_url="https://www.quora.com/profile/{username}",
        description="Public Q&A author profile, answered questions, and knowledge followers.",
        category="community",
        access_type="public_web",
        limitations=["Public answers and questions."],
        license="MIT",
    )
    url_pattern = "https://www.quora.com/profile/{username}"
    soft_404_indicators = ["Page Not Found", "Quora - Page Not Found", "No results found"]


class DiscourseMetaUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.discourse_meta",
        name="Discourse Meta",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Discourse Meta Community",
        source_url="https://meta.discourse.org/u/{username}",
        description="Discourse platform flagship community user profile, badges, and trust level.",
        category="community",
        access_type="public_api",
        limitations=["Public trust level and posts."],
        license="MIT",
    )
    url_pattern = "https://meta.discourse.org/u/{username}.json"
    profile_url_pattern = "https://meta.discourse.org/u/{username}"
    is_json_api = True
    json_required_keys = ["user"]


class FDroidForumUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.fdroid_forum",
        name="F-Droid Forum",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="F-Droid Community",
        source_url="https://forum.f-droid.org/u/{username}",
        description="Free and open-source Android app repository forum community member.",
        category="community",
        access_type="public_api",
        limitations=["Public community profile."],
        license="MIT",
    )
    url_pattern = "https://forum.f-droid.org/u/{username}.json"
    profile_url_pattern = "https://forum.f-droid.org/u/{username}"
    is_json_api = True
    json_required_keys = ["user"]


class BitwardenForumUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.bitwarden_forum",
        name="Bitwarden Community",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Bitwarden Community Forums",
        source_url="https://community.bitwarden.com/u/{username}",
        description="Bitwarden open-source password manager community discussion profile.",
        category="community",
        access_type="public_api",
        limitations=["Public community badges."],
        license="MIT",
    )
    url_pattern = "https://community.bitwarden.com/u/{username}.json"
    profile_url_pattern = "https://community.bitwarden.com/u/{username}"
    is_json_api = True
    json_required_keys = ["user"]


class SpeedrunUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.speedrun",
        name="Speedrun.com",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Speedrun.com",
        source_url="https://www.speedrun.com/users/{username}",
        description="Video game speedrun records, leaderboards, and verified personal bests.",
        category="gaming",
        access_type="public_api",
        limitations=["Public speedrun leaderboard runs."],
        license="MIT",
    )
    url_pattern = "https://www.speedrun.com/api/v1/users/{username}"
    profile_url_pattern = "https://www.speedrun.com/users/{username}"
    is_json_api = True
    json_required_keys = ["data"]


class RobloxUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.roblox",
        name="Roblox",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Roblox",
        source_url="https://www.roblox.com/user.aspx?username={username}",
        description="Roblox gaming avatar, creator experiences, and group memberships.",
        category="gaming",
        access_type="public_web",
        limitations=["Public avatar and inventory."],
        license="MIT",
    )
    url_pattern = "https://www.roblox.com/user.aspx?username={username}"
    soft_404_indicators = ["Page cannot be found", "Cannot find member", "User Not Found"]


class OsuUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.osu",
        name="osu!",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="osu! Rhythm Game",
        source_url="https://osu.ppy.sh/users/{username}",
        description="Rhythm game player performance points (pp), global rank, and beatmaps.",
        category="gaming",
        access_type="public_web",
        limitations=["Public player ranking."],
        license="MIT",
    )
    url_pattern = "https://osu.ppy.sh/users/{username}"


class NameMCUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.namemc",
        name="NameMC (Minecraft)",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="NameMC",
        source_url="https://namemc.com/profile/{username}",
        description="Minecraft player skin gallery, capes, and username history.",
        category="gaming",
        access_type="public_web",
        limitations=["Public skin and past handles."],
        license="MIT",
    )
    url_pattern = "https://namemc.com/profile/{username}"


class KongregateUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.kongregate",
        name="Kongregate",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Kongregate",
        source_url="https://www.kongregate.com/accounts/{username}",
        description="Web gaming community profile, player level, and game badges.",
        category="gaming",
        access_type="public_web",
        limitations=["Public player achievements."],
        license="MIT",
    )
    url_pattern = "https://www.kongregate.com/accounts/{username}"
    soft_404_indicators = ["Page Not Found", "Sign Up For Kongregate", "User not found"]


class NewgroundsUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.newgrounds",
        name="Newgrounds",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Newgrounds",
        source_url="https://{username}.newgrounds.com",
        description="Flash animation, indie games, digital audio, and art community profile.",
        category="gaming",
        access_type="public_web",
        limitations=["Public creator portal."],
        license="MIT",
    )
    url_pattern = "https://{username}.newgrounds.com"
    soft_404_indicators = [
        "Page not found",
        "Sorry, that user could not be found",
        "404 - Not Found",
    ]


class WikiquoteUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.wikiquote",
        name="Wikiquote User",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Wikiquote",
        source_url="https://en.wikiquote.org/wiki/User:{username}",
        description="Wikiquote quotation compendium registered editor user page.",
        category="community",
        access_type="public_web",
        limitations=["Public editor page."],
        license="MIT",
    )
    url_pattern = "https://en.wikiquote.org/wiki/User:{username}"
    soft_404_indicators = [
        "does not have a user page",
        "does not exist",
        "There is currently no text in this page",
    ]


class WiktionaryUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.wiktionary",
        name="Wiktionary User",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Wiktionary",
        source_url="https://en.wiktionary.org/wiki/User:{username}",
        description="Collaborative multilingual dictionary editor user page.",
        category="community",
        access_type="public_web",
        limitations=["Public editor page."],
        license="MIT",
    )
    url_pattern = "https://en.wiktionary.org/wiki/User:{username}"
    soft_404_indicators = [
        "does not have a user page",
        "does not exist",
        "There is currently no text in this page",
    ]


class WikivoyageUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.wikivoyage",
        name="Wikivoyage User",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Wikivoyage",
        source_url="https://en.wikivoyage.org/wiki/User:{username}",
        description="Open travel guide contributor and editor user page.",
        category="community",
        access_type="public_web",
        limitations=["Public editor page."],
        license="MIT",
    )
    url_pattern = "https://en.wikivoyage.org/wiki/User:{username}"
    soft_404_indicators = [
        "does not have a user page",
        "does not exist",
        "There is currently no text in this page",
    ]


class WordPressUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.wordpress",
        name="WordPress.com",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="WordPress.com",
        source_url="https://{username}.wordpress.com",
        description="WordPress hosted blog and publishing website subdomain.",
        category="blogging",
        access_type="public_web",
        limitations=["Public blog site."],
        license="MIT",
    )
    url_pattern = "https://{username}.wordpress.com"
    soft_404_indicators = ["doesn’t exist", "Do you want to register", "does not exist"]


class BloggerUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.blogger",
        name="Blogger (Blogspot)",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Blogger",
        source_url="https://{username}.blogspot.com",
        description="Google Blogger blog publication subdomain.",
        category="blogging",
        access_type="public_web",
        limitations=["Public blog subdomain."],
        license="MIT",
    )
    url_pattern = "https://{username}.blogspot.com"
    soft_404_indicators = [
        "does not exist",
        "Blog not found",
        "The blog you were looking for does not exist",
    ]


class LiveJournalUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.livejournal",
        name="LiveJournal",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="LiveJournal",
        source_url="https://{username}.livejournal.com",
        description="Personal blogging journal entries and community posts.",
        category="blogging",
        access_type="public_web",
        limitations=["Public journal posts."],
        license="MIT",
    )
    url_pattern = "https://{username}.livejournal.com"
    soft_404_indicators = ["Unknown user", "User not found", "community does not exist"]


class TelegraphUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.telegraph",
        name="Telegra.ph",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Telegra.ph (Telegram)",
        source_url="https://telegra.ph/{username}",
        description="Minimalist anonymous publishing publication on Telegra.ph.",
        category="blogging",
        access_type="public_web",
        limitations=["Public articles."],
        license="MIT",
    )
    url_pattern = "https://telegra.ph/{username}"


class VeroUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.vero",
        name="Vero",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Vero Social",
        source_url="https://vero.co/{username}",
        description="Subscription-free creator and social network profile.",
        category="social",
        access_type="public_web",
        limitations=["Public user profile."],
        license="MIT",
    )
    url_pattern = "https://vero.co/{username}"


class GravatarProfileUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.gravatar_profile",
        name="Gravatar Public Profile",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Gravatar Profiles",
        source_url="https://en.gravatar.com/{username}",
        description="Public Gravatar biography, verified social links, and avatars.",
        category="community",
        access_type="public_api",
        limitations=["Public profile entries."],
        license="MIT",
    )
    url_pattern = "https://en.gravatar.com/{username}.json"
    profile_url_pattern = "https://en.gravatar.com/{username}"
    is_json_api = True
    json_required_keys = ["entry"]


class OpenSeaUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.opensea",
        name="OpenSea",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="OpenSea Marketplace",
        source_url="https://opensea.io/{username}",
        description="Digital collectibles, NFT collections, and web3 creator profile.",
        category="community",
        access_type="public_web",
        limitations=["Public collection items."],
        license="MIT",
    )
    url_pattern = "https://opensea.io/{username}"
    soft_404_indicators = ["404 - OpenSea", "This page couldn't be found", "Page not found"]


class TrelloUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.trello",
        name="Trello",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Atlassian Trello",
        source_url="https://trello.com/{username}",
        description="Kanban project management public profile and public boards.",
        category="community",
        access_type="public_web",
        limitations=["Public profile cards."],
        license="MIT",
    )
    url_pattern = "https://trello.com/{username}"


class SpigotMCUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.spigotmc",
        name="SpigotMC",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="SpigotMC Minecraft Community",
        source_url="https://www.spigotmc.org/members/{username}/",
        description="Minecraft server developer, plugin author, and community member.",
        category="gaming",
        access_type="public_web",
        limitations=["Public forum profile."],
        license="MIT",
    )
    url_pattern = "https://www.spigotmc.org/members/{username}/"


class NexusModsUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.nexusmods",
        name="Nexus Mods",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Nexus Mods",
        source_url="https://www.nexusmods.com/users/{username}",
        description="Video game mod creator, published game mods, and author endorsements.",
        category="gaming",
        access_type="public_web",
        limitations=["Public author profile."],
        license="MIT",
    )
    url_pattern = "https://www.nexusmods.com/users/{username}"


class ScratchForumUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.scratch_community",
        name="Scratch Community",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Scratch Community",
        source_url="https://scratch.mit.edu/users/{username}/",
        description="MIT Scratch student and educator creator gallery and community.",
        category="community",
        access_type="public_web",
        limitations=["Public studios and favorites."],
        license="MIT",
    )
    url_pattern = "https://scratch.mit.edu/users/{username}/"
    soft_404_indicators = ["Page not found", "Could not find that page", "404 - Scratch"]


class SpeedrunWRUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.speedrun_profile",
        name="Speedrun Leaderboard",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Speedrun Leaderboard",
        source_url="https://www.speedrun.com/user/{username}",
        description="Competitive video game speedrunning profile and world records.",
        category="gaming",
        access_type="public_web",
        limitations=["Public runner profile."],
        license="MIT",
    )
    url_pattern = "https://www.speedrun.com/user/{username}"
    soft_404_indicators = ["User not found", "404 - Not Found", "Page Not Found"]
