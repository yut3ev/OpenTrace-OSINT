"""Sherlock-adapted creative, portfolio, media, and audio platform adapters (MIT Licensed)."""

from __future__ import annotations

from opentrace.api.schemas.common import TargetType
from opentrace.modules.base import BaseUsernameAdapter, ModuleMetadata


class DeviantArtUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.deviantart",
        name="DeviantArt",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="DeviantArt",
        source_url="https://www.deviantart.com/{username}",
        description="Digital art, illustrations, and artist portfolio gallery on DeviantArt.",
        category="creative",
        access_type="public_web",
        limitations=["Public art gallery only."],
        license="MIT",
    )
    url_pattern = "https://www.deviantart.com/{username}"
    soft_404_indicators = ["404 Not Found", "Deactivated Account", "Page Not Found"]


class ArtStationUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.artstation",
        name="ArtStation",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="ArtStation",
        source_url="https://www.artstation.com/{username}",
        description="Professional concept art, 3D modeling, and visual arts portfolio.",
        category="creative",
        access_type="public_web",
        limitations=["Public portfolio."],
        license="MIT",
    )
    url_pattern = "https://www.artstation.com/{username}"
    soft_404_indicators = ["404 - Not Found", "Page not found", "Artist not found"]


class FiveHundredPxUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.500px",
        name="500px",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="500px Photography",
        source_url="https://500px.com/p/{username}",
        description="Professional photography portfolio and camera galleries.",
        category="creative",
        access_type="public_web",
        limitations=["Public photo stream."],
        license="MIT",
    )
    url_pattern = "https://500px.com/p/{username}"
    soft_404_indicators = ["Page Not Found", "404 - 500px", "User Not Found"]


class MixcloudUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.mixcloud",
        name="Mixcloud",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Mixcloud",
        source_url="https://www.mixcloud.com/{username}/",
        description="DJ radio shows, audio podcasts, and live DJ sets.",
        category="audio",
        access_type="public_api",
        limitations=["Public audio shows."],
        license="MIT",
    )
    url_pattern = "https://api.mixcloud.com/{username}/"
    profile_url_pattern = "https://www.mixcloud.com/{username}/"
    is_json_api = True
    json_required_keys = ["username"]


class AudiomackUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.audiomack",
        name="Audiomack",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Audiomack",
        source_url="https://audiomack.com/{username}",
        description="Music artist songs, albums, and mixtape streaming profile.",
        category="audio",
        access_type="public_web",
        limitations=["Public artist songs."],
        license="MIT",
    )
    url_pattern = "https://audiomack.com/{username}"
    soft_404_indicators = ["Page Not Found", "404 - Audiomack", "Artist not found"]


class ReverbNationUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.reverbnation",
        name="ReverbNation",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="ReverbNation",
        source_url="https://www.reverbnation.com/{username}",
        description="Independent music band and musician profile and gigs.",
        category="audio",
        access_type="public_web",
        limitations=["Public artist discography."],
        license="MIT",
    )
    url_pattern = "https://www.reverbnation.com/{username}"
    soft_404_indicators = ["Sorry, we couldn't find that page", "Page Not Found", "404"]


class FreesoundUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.freesound",
        name="Freesound",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Freesound.org",
        source_url="https://freesound.org/people/{username}/",
        description="Creative Commons audio samples and field sound recordings author.",
        category="audio",
        access_type="public_web",
        limitations=["Public audio samples."],
        license="MIT",
    )
    url_pattern = "https://freesound.org/people/{username}/"
    soft_404_indicators = ["404 - Page not found", "User does not exist"]


class SmugMugUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.smugmug",
        name="SmugMug",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="SmugMug",
        source_url="https://{username}.smugmug.com/",
        description="Photography gallery showcase and custom photo site.",
        category="creative",
        access_type="public_web",
        limitations=["Public photo site."],
        license="MIT",
    )
    url_pattern = "https://{username}.smugmug.com/"
    soft_404_indicators = ["Page Not Found", "Owner has not set up", "Site Not Found"]


class PixivUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.pixiv",
        name="Pixiv",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Pixiv",
        source_url="https://www.pixiv.net/users/{username}",
        description="Japanese and international manga, anime, and digital art community.",
        category="creative",
        access_type="public_web",
        limitations=["Public art submissions."],
        license="MIT",
    )
    url_pattern = "https://www.pixiv.net/users/{username}"
    soft_404_indicators = ["User not found", "error-title", "404 Not Found"]


class WattpadUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.wattpad",
        name="Wattpad",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Wattpad",
        source_url="https://www.wattpad.com/user/{username}",
        description="Social storytelling, fiction novels, and writer profile.",
        category="creative",
        access_type="public_web",
        limitations=["Public reading lists and stories."],
        license="MIT",
    )
    url_pattern = "https://www.wattpad.com/user/{username}"
    soft_404_indicators = ["User Not Found", "page-not-found", "404 Not Found"]


class ArchiveOrgUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.archive_org",
        name="Internet Archive",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Internet Archive (archive.org)",
        source_url="https://archive.org/details/@{username}",
        description="Public digital library media uploads, books, and web archives.",
        category="creative",
        access_type="public_web",
        limitations=["Public collection items."],
        license="MIT",
    )
    url_pattern = "https://archive.org/details/@{username}"
    soft_404_indicators = ["cannot be found", "Item cannot be found", "The item is not available"]


class ItchIoUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.itchio",
        name="itch.io",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="itch.io Indie Games",
        source_url="https://{username}.itch.io",
        description="Indie video games creator, game jams, and asset developer page.",
        category="gaming",
        access_type="public_web",
        limitations=["Published game projects."],
        license="MIT",
    )
    url_pattern = "https://{username}.itch.io"
    soft_404_indicators = ["Page not found", "404 - itch.io", "There’s nothing here"]


class AudioboomUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.audioboom",
        name="Audioboom",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Audioboom Podcasts",
        source_url="https://audioboom.com/users/{username}",
        description="Spoken word and commercial podcast publisher profile.",
        category="audio",
        access_type="public_web",
        limitations=["Public episodes."],
        license="MIT",
    )
    url_pattern = "https://audioboom.com/users/{username}"


class InstructablesUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.instructables",
        name="Instructables",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Autodesk Instructables",
        source_url="https://www.instructables.com/member/{username}/",
        description="DIY maker projects, electronics circuits, and workshop guides.",
        category="creative",
        access_type="public_web",
        limitations=["Public instructables."],
        license="MIT",
    )
    url_pattern = "https://www.instructables.com/member/{username}/"


class BandcampFansUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.bandcamp_fans",
        name="Bandcamp Fan Collection",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Bandcamp",
        source_url="https://bandcamp.com/{username}",
        description="Music fan collection, wishlists, and supported indie artists.",
        category="audio",
        access_type="public_web",
        limitations=["Public music collection."],
        license="MIT",
    )
    url_pattern = "https://bandcamp.com/{username}"


class TraktUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.trakt",
        name="Trakt.tv",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Trakt.tv",
        source_url="https://trakt.tv/users/{username}",
        description="Television series and movie watch tracking diary and ratings.",
        category="media",
        access_type="public_web",
        limitations=["Public scrobbles."],
        license="MIT",
    )
    url_pattern = "https://trakt.tv/users/{username}"


class MyAnimeListUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.myanimelist",
        name="MyAnimeList",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="MyAnimeList",
        source_url="https://myanimelist.net/profile/{username}",
        description="Anime and manga list tracking, scores, and forum history.",
        category="media",
        access_type="public_web",
        limitations=["Public profile."],
        license="MIT",
    )
    url_pattern = "https://myanimelist.net/profile/{username}"


class AniListUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.anilist",
        name="AniList",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="AniList",
        source_url="https://anilist.co/user/{username}/",
        description="Social anime and manga discovery, stats, and reviews.",
        category="media",
        access_type="public_web",
        limitations=["Public statistics."],
        license="MIT",
    )
    url_pattern = "https://anilist.co/user/{username}/"
    soft_404_indicators = ["Page Not Found", "404 - AniList", "User not found"]


class BoardGameGeekUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.boardgamegeek",
        name="BoardGameGeek",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="BoardGameGeek (BGG)",
        source_url="https://boardgamegeek.com/user/{username}",
        description="Board game collection, plays logged, and guild memberships.",
        category="gaming",
        access_type="public_web",
        limitations=["Public game plays."],
        license="MIT",
    )
    url_pattern = "https://boardgamegeek.com/user/{username}"
    soft_404_indicators = ["Invalid user", "User does not exist", "Page Not Found"]


class ChessgamesUsernameModule(BaseUsernameAdapter):
    metadata = ModuleMetadata(
        id="username.chessgames",
        name="Chessgames.com",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Chessgames.com",
        source_url="https://www.chessgames.com/perl/chessplayer?pid={username}",
        description="Historical and master chess games player database.",
        category="gaming",
        access_type="public_web",
        limitations=["Master chess game records."],
        license="MIT",
    )
    url_pattern = "https://www.chessgames.com/perl/chessplayer?pid={username}"
    soft_404_indicators = ["player not found", "No matches found", "Error: Player not found"]
