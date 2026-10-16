"""Module registry for discovering, validating, and managing OSINT modules."""

from __future__ import annotations

import logging

from opentrace.api.schemas.common import TargetType
from opentrace.core.errors import ModuleError
from opentrace.modules.base import OSINTModule
from opentrace.modules.email.disposable import DisposableEmailModule
from opentrace.modules.email.dns import EmailDNSModule
from opentrace.modules.email.extended_email import (
    CrossrefAuthorEmailModule,
    GitHubCommitsEmailModule,
    HunterVerifierEmailModule,
    PgpKeyserverEmailModule,
)
from opentrace.modules.email.free_osint import (
    EmailCertificateTransparencyModule,
    EmailRDAPDomainModule,
    EmailSecurityTxtModule,
)
from opentrace.modules.email.gravatar import GravatarEmailModule
from opentrace.modules.email.hibp import HaveIBeenPwnedEmailModule
from opentrace.modules.email.security import EmailSecurityModule
from opentrace.modules.email.syntax import EmailSyntaxModule
from opentrace.modules.people.dblp import DblpAuthorModule
from opentrace.modules.people.extended_people import (
    ArxivAuthorModule,
    CrossrefAuthorModule,
    SearchQueryGeneratorModule,
)
from opentrace.modules.people.free_people import (
    SemanticScholarAuthorModule,
    WikidataEntityModule,
    WikipediaFullTextSearchModule,
)
from opentrace.modules.people.openalex import OpenAlexAuthorModule
from opentrace.modules.people.wikipedia import WikipediaPersonModule
from opentrace.modules.phone.extended_phone import (
    PhoneCarrierPrefixModule,
    PhoneHlrLookupModule,
    PhoneInternationalModule,
)
from opentrace.modules.phone.free_phone import (
    PhoneTimezoneModule,
    PhoneValidationRulesModule,
)
from opentrace.modules.phone.numbering import PhoneNumberingModule
from opentrace.modules.phone.provider import AuthorizedPhoneLookupModule
from opentrace.modules.usernames.developer import (
    BitbucketUsernameModule,
    DevToUsernameModule,
    DockerHubUsernameModule,
    HuggingFaceUsernameModule,
    NpmUsernameModule,
    PyPIUsernameModule,
)
from opentrace.modules.usernames.extended_dev import (
    CodebergUsernameModule,
    CratesIoUsernameModule,
    HashnodeUsernameModule,
    KaggleUsernameModule,
    PackagistUsernameModule,
    ReplitUsernameModule,
    RubyGemsUsernameModule,
    SourceForgeUsernameModule,
    StackExchangeUsernameModule,
)
from opentrace.modules.usernames.extended_gaming import (
    CodeforcesUsernameModule,
    DuolingoUsernameModule,
    GoodreadsUsernameModule,
    LastFmUsernameModule,
    LeetCodeUsernameModule,
    LetterboxdUsernameModule,
    SteamUsernameModule,
    StravaUsernameModule,
    TelegramUsernameModule,
    TryHackMeUsernameModule,
    TwitchUsernameModule,
)
from opentrace.modules.usernames.extended_social import (
    AboutMeUsernameModule,
    BandcampUsernameModule,
    BehanceUsernameModule,
    BuyMeACoffeeUsernameModule,
    DevpostUsernameModule,
    DisqusUsernameModule,
    DribbbleUsernameModule,
    FlickrUsernameModule,
    LinktreeUsernameModule,
    MediumUsernameModule,
    PatreonUsernameModule,
    PinterestUsernameModule,
    ProductHuntUsernameModule,
    SoundCloudUsernameModule,
    SubstackUsernameModule,
    TumblrUsernameModule,
    VimeoUsernameModule,
)
from opentrace.modules.usernames.gaming_community import (
    ChessComUsernameModule,
    HackerNewsUsernameModule,
    LichessUsernameModule,
    WikipediaUserModule,
)
from opentrace.modules.usernames.github import GitHubUsernameModule
from opentrace.modules.usernames.gitlab import GitLabUsernameModule
from opentrace.modules.usernames.sherlock_community import (
    BitwardenForumUsernameModule,
    BloggerUsernameModule,
    DiscourseMetaUsernameModule,
    FDroidForumUsernameModule,
    GravatarProfileUsernameModule,
    KongregateUsernameModule,
    LiveJournalUsernameModule,
    NameMCUsernameModule,
    NewgroundsUsernameModule,
    NexusModsUsernameModule,
    OpenSeaUsernameModule,
    OsuUsernameModule,
    QuoraUsernameModule,
    RobloxUsernameModule,
    ScratchForumUsernameModule,
    SpeedrunUsernameModule,
    SpeedrunWRUsernameModule,
    SpigotMCUsernameModule,
    TelegraphUsernameModule,
    TrelloUsernameModule,
    VeroUsernameModule,
    WikiquoteUsernameModule,
    WikivoyageUsernameModule,
    WiktionaryUsernameModule,
    WordPressUsernameModule,
)
from opentrace.modules.usernames.sherlock_creative import (
    AniListUsernameModule,
    ArchiveOrgUsernameModule,
    ArtStationUsernameModule,
    AudioboomUsernameModule,
    AudiomackUsernameModule,
    BandcampFansUsernameModule,
    BoardGameGeekUsernameModule,
    ChessgamesUsernameModule,
    DeviantArtUsernameModule,
    FiveHundredPxUsernameModule,
    FreesoundUsernameModule,
    InstructablesUsernameModule,
    ItchIoUsernameModule,
    MixcloudUsernameModule,
    MyAnimeListUsernameModule,
    PixivUsernameModule,
    ReverbNationUsernameModule,
    SmugMugUsernameModule,
    TraktUsernameModule,
    WattpadUsernameModule,
)
from opentrace.modules.usernames.sherlock_developer import (
    AnkiWebUsernameModule,
    AsciinemaUsernameModule,
    BugcrowdUsernameModule,
    CodecademyUsernameModule,
    CoderwallUsernameModule,
    CodewarsUsernameModule,
    ExercismUsernameModule,
    FreeCodeCampUsernameModule,
    GeeksforGeeksUsernameModule,
    GiteaUsernameModule,
    HackerRankUsernameModule,
    HackTheBoxUsernameModule,
    LaunchpadUsernameModule,
    LobstersUsernameModule,
    PastebinUsernameModule,
    ScratchUsernameModule,
    SourceHutUsernameModule,
    TopcoderUsernameModule,
    WakatimeUsernameModule,
    WeblateUsernameModule,
)
from opentrace.modules.usernames.social import (
    BlueskyUsernameModule,
    KeybaseUsernameModule,
    MastodonUsernameModule,
    RedditUsernameModule,
)
from opentrace.modules.web.search import DuckDuckGoInstantModule, OpenWebSearchModule

logger = logging.getLogger("opentrace.modules.registry")


class ModuleRegistry:
    """Registry maintaining all available and active OSINT modules."""

    def __init__(self) -> None:
        self._modules: dict[str, OSINTModule] = {}

    def register(self, module: OSINTModule) -> None:
        """Register a module instance. Verifies unique ID."""
        meta = module.metadata
        if meta.id in self._modules:
            raise ModuleError(
                f"Module with ID '{meta.id}' is already registered.",
                module_id=meta.id,
            )
        self._modules[meta.id] = module
        logger.debug("Registered module '%s' (%s)", meta.id, meta.name)

    def get(self, module_id: str) -> OSINTModule | None:
        """Retrieve a registered module by its ID."""
        return self._modules.get(module_id)

    def list_all(self) -> list[OSINTModule]:
        """Return all registered modules."""
        return list(self._modules.values())

    def list_for_target(self, target_type: TargetType | str) -> list[OSINTModule]:
        """Return all enabled modules supporting the specified target type."""
        target_val = target_type.value if isinstance(target_type, TargetType) else target_type
        return [m for m in self._modules.values() if m.metadata.enabled and m.supports(target_val)]

    def clear(self) -> None:
        """Clear all registered modules."""
        self._modules.clear()


_default_registry: ModuleRegistry | None = None


def get_default_registry() -> ModuleRegistry:
    """Return the populated default registry containing all verified modules."""
    global _default_registry
    if _default_registry is None:
        reg = ModuleRegistry()

        # ------------------------------------------------------------------
        # USERNAME ADAPTERS (Core & Extended)
        # ------------------------------------------------------------------
        # Core Developer
        reg.register(GitHubUsernameModule())
        reg.register(GitLabUsernameModule())
        reg.register(BitbucketUsernameModule())
        reg.register(DockerHubUsernameModule())
        reg.register(PyPIUsernameModule())
        reg.register(NpmUsernameModule())
        reg.register(HuggingFaceUsernameModule())
        reg.register(DevToUsernameModule())

        # Extended Developer
        reg.register(CodebergUsernameModule())
        reg.register(HashnodeUsernameModule())
        reg.register(KaggleUsernameModule())
        reg.register(ReplitUsernameModule())
        reg.register(SourceForgeUsernameModule())
        reg.register(PackagistUsernameModule())
        reg.register(RubyGemsUsernameModule())
        reg.register(CratesIoUsernameModule())
        reg.register(StackExchangeUsernameModule())

        # Core Social
        reg.register(MastodonUsernameModule())
        reg.register(BlueskyUsernameModule())
        reg.register(RedditUsernameModule())
        reg.register(KeybaseUsernameModule())

        # Extended Social, Creator, & Publishing
        reg.register(MediumUsernameModule())
        reg.register(SubstackUsernameModule())
        reg.register(TumblrUsernameModule())
        reg.register(DisqusUsernameModule())
        reg.register(ProductHuntUsernameModule())
        reg.register(DevpostUsernameModule())
        reg.register(AboutMeUsernameModule())
        reg.register(LinktreeUsernameModule())
        reg.register(BuyMeACoffeeUsernameModule())
        reg.register(PatreonUsernameModule())
        reg.register(PinterestUsernameModule())
        reg.register(FlickrUsernameModule())
        reg.register(VimeoUsernameModule())
        reg.register(SoundCloudUsernameModule())
        reg.register(BandcampUsernameModule())
        reg.register(BehanceUsernameModule())
        reg.register(DribbbleUsernameModule())

        # Core Gaming & Community
        reg.register(ChessComUsernameModule())
        reg.register(LichessUsernameModule())
        reg.register(HackerNewsUsernameModule())
        reg.register(WikipediaUserModule())

        # Extended Gaming, Security, & Competitive
        reg.register(SteamUsernameModule())
        reg.register(TwitchUsernameModule())
        reg.register(GoodreadsUsernameModule())
        reg.register(LetterboxdUsernameModule())
        reg.register(LastFmUsernameModule())
        reg.register(StravaUsernameModule())
        reg.register(DuolingoUsernameModule())
        reg.register(TryHackMeUsernameModule())
        reg.register(LeetCodeUsernameModule())
        reg.register(CodeforcesUsernameModule())
        reg.register(TelegramUsernameModule())

        # Sherlock Developer Platforms (MIT)
        reg.register(HackerRankUsernameModule())
        reg.register(CodewarsUsernameModule())
        reg.register(CodecademyUsernameModule())
        reg.register(GeeksforGeeksUsernameModule())
        reg.register(TopcoderUsernameModule())
        reg.register(WakatimeUsernameModule())
        reg.register(HackTheBoxUsernameModule())
        reg.register(BugcrowdUsernameModule())
        reg.register(LaunchpadUsernameModule())
        reg.register(AsciinemaUsernameModule())
        reg.register(AnkiWebUsernameModule())
        reg.register(FreeCodeCampUsernameModule())
        reg.register(CoderwallUsernameModule())
        reg.register(LobstersUsernameModule())
        reg.register(ScratchUsernameModule())
        reg.register(ExercismUsernameModule())
        reg.register(WeblateUsernameModule())
        reg.register(GiteaUsernameModule())
        reg.register(SourceHutUsernameModule())
        reg.register(PastebinUsernameModule())

        # Sherlock Creative, Audio & Media Platforms (MIT)
        reg.register(DeviantArtUsernameModule())
        reg.register(ArtStationUsernameModule())
        reg.register(FiveHundredPxUsernameModule())
        reg.register(MixcloudUsernameModule())
        reg.register(AudiomackUsernameModule())
        reg.register(ReverbNationUsernameModule())
        reg.register(FreesoundUsernameModule())
        reg.register(SmugMugUsernameModule())
        reg.register(PixivUsernameModule())
        reg.register(WattpadUsernameModule())
        reg.register(ArchiveOrgUsernameModule())
        reg.register(ItchIoUsernameModule())
        reg.register(AudioboomUsernameModule())
        reg.register(InstructablesUsernameModule())
        reg.register(BandcampFansUsernameModule())
        reg.register(TraktUsernameModule())
        reg.register(MyAnimeListUsernameModule())
        reg.register(AniListUsernameModule())
        reg.register(BoardGameGeekUsernameModule())
        reg.register(ChessgamesUsernameModule())

        # Sherlock Community, Forums & Gaming Platforms (MIT)
        reg.register(QuoraUsernameModule())
        reg.register(DiscourseMetaUsernameModule())
        reg.register(FDroidForumUsernameModule())
        reg.register(BitwardenForumUsernameModule())
        reg.register(SpeedrunUsernameModule())
        reg.register(RobloxUsernameModule())
        reg.register(OsuUsernameModule())
        reg.register(NameMCUsernameModule())
        reg.register(KongregateUsernameModule())
        reg.register(NewgroundsUsernameModule())
        reg.register(WikiquoteUsernameModule())
        reg.register(WiktionaryUsernameModule())
        reg.register(WikivoyageUsernameModule())
        reg.register(WordPressUsernameModule())
        reg.register(BloggerUsernameModule())
        reg.register(LiveJournalUsernameModule())
        reg.register(TelegraphUsernameModule())
        reg.register(VeroUsernameModule())
        reg.register(GravatarProfileUsernameModule())
        reg.register(OpenSeaUsernameModule())
        reg.register(TrelloUsernameModule())
        reg.register(SpigotMCUsernameModule())
        reg.register(NexusModsUsernameModule())
        reg.register(ScratchForumUsernameModule())
        reg.register(SpeedrunWRUsernameModule())

        # ------------------------------------------------------------------
        # EMAIL ADAPTERS (Core & Extended)
        # ------------------------------------------------------------------
        reg.register(EmailSyntaxModule())
        reg.register(EmailDNSModule())
        reg.register(DisposableEmailModule())
        reg.register(GravatarEmailModule())
        reg.register(EmailSecurityModule())
        reg.register(HaveIBeenPwnedEmailModule())
        reg.register(GitHubCommitsEmailModule())
        reg.register(PgpKeyserverEmailModule())
        reg.register(CrossrefAuthorEmailModule())
        reg.register(HunterVerifierEmailModule())
        reg.register(EmailRDAPDomainModule())
        reg.register(EmailSecurityTxtModule())
        reg.register(EmailCertificateTransparencyModule())

        # ------------------------------------------------------------------
        # PHONE ADAPTERS (Core & Extended)
        # ------------------------------------------------------------------
        reg.register(PhoneNumberingModule())
        reg.register(AuthorizedPhoneLookupModule())
        reg.register(PhoneInternationalModule())
        reg.register(PhoneCarrierPrefixModule())
        reg.register(PhoneHlrLookupModule())
        reg.register(PhoneTimezoneModule())
        reg.register(PhoneValidationRulesModule())

        # ------------------------------------------------------------------
        # PEOPLE & PUBLIC SCHOLAR ADAPTERS (Core & Extended)
        # ------------------------------------------------------------------
        reg.register(WikipediaPersonModule())
        reg.register(DblpAuthorModule())
        reg.register(OpenAlexAuthorModule())
        reg.register(CrossrefAuthorModule())
        reg.register(ArxivAuthorModule())
        reg.register(SearchQueryGeneratorModule())
        reg.register(WikidataEntityModule())
        reg.register(SemanticScholarAuthorModule())
        reg.register(WikipediaFullTextSearchModule())

        # ------------------------------------------------------------------
        # WEB SEARCH ADAPTERS
        # ------------------------------------------------------------------
        reg.register(DuckDuckGoInstantModule())
        reg.register(OpenWebSearchModule())

        _default_registry = reg
    return _default_registry
