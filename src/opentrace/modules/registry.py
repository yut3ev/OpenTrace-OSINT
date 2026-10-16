"""Module registry for discovering, validating, and managing OSINT modules."""

from __future__ import annotations

import logging

from opentrace.api.schemas.common import TargetType
from opentrace.core.errors import ModuleError
from opentrace.modules.base import OSINTModule
from opentrace.modules.email.disposable import DisposableEmailModule
from opentrace.modules.email.dns import EmailDNSModule
from opentrace.modules.email.gravatar import GravatarEmailModule
from opentrace.modules.email.security import EmailSecurityModule
from opentrace.modules.email.syntax import EmailSyntaxModule
from opentrace.modules.people.dblp import DblpAuthorModule
from opentrace.modules.people.openalex import OpenAlexAuthorModule
from opentrace.modules.people.wikipedia import WikipediaPersonModule
from opentrace.modules.phone.numbering import PhoneNumberingModule
from opentrace.modules.usernames.developer import (
    BitbucketUsernameModule,
    DevToUsernameModule,
    DockerHubUsernameModule,
    HuggingFaceUsernameModule,
    NpmUsernameModule,
    PyPIUsernameModule,
)
from opentrace.modules.usernames.gaming_community import (
    ChessComUsernameModule,
    HackerNewsUsernameModule,
    LichessUsernameModule,
    WikipediaUserModule,
)
from opentrace.modules.usernames.github import GitHubUsernameModule
from opentrace.modules.usernames.gitlab import GitLabUsernameModule
from opentrace.modules.usernames.social import (
    BlueskyUsernameModule,
    KeybaseUsernameModule,
    MastodonUsernameModule,
    RedditUsernameModule,
)

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
        # Username modules
        reg.register(GitHubUsernameModule())
        reg.register(GitLabUsernameModule())
        reg.register(BitbucketUsernameModule())
        reg.register(DockerHubUsernameModule())
        reg.register(PyPIUsernameModule())
        reg.register(NpmUsernameModule())
        reg.register(HuggingFaceUsernameModule())
        reg.register(DevToUsernameModule())
        reg.register(MastodonUsernameModule())
        reg.register(BlueskyUsernameModule())
        reg.register(RedditUsernameModule())
        reg.register(KeybaseUsernameModule())
        reg.register(ChessComUsernameModule())
        reg.register(LichessUsernameModule())
        reg.register(HackerNewsUsernameModule())
        reg.register(WikipediaUserModule())

        # Email modules
        reg.register(EmailSyntaxModule())
        reg.register(EmailDNSModule())
        reg.register(DisposableEmailModule())
        reg.register(GravatarEmailModule())
        reg.register(EmailSecurityModule())

        # Phone modules
        reg.register(PhoneNumberingModule())

        # People / Name modules
        reg.register(WikipediaPersonModule())
        reg.register(DblpAuthorModule())
        reg.register(OpenAlexAuthorModule())

        _default_registry = reg
    return _default_registry
