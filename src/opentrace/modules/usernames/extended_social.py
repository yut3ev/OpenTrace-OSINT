"""Extended social, blogging, publishing, and creator platform adapters."""

from __future__ import annotations

from opentrace.api.schemas.common import TargetType
from opentrace.modules.base import BaseUsernameAdapter, ModuleMetadata


class MediumUsernameModule(BaseUsernameAdapter):
    """Verifies public author profiles on Medium publishing platform."""

    metadata = ModuleMetadata(
        id="username.medium",
        name="Medium",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Medium",
        source_url="https://medium.com/@{username}",
        description="Public Medium author profile, stories, and publications.",
        category="blogging",
        access_type="public_web",
        limitations=["Custom publication domains may not resolve directly"],
    )
    url_pattern = "https://medium.com/@{username}"
    soft_404_indicators = ["PAGE NOT FOUND", "404", "Out of nothing, something.", "User not found"]


class SubstackUsernameModule(BaseUsernameAdapter):
    """Verifies newsletter publications on Substack."""

    metadata = ModuleMetadata(
        id="username.substack",
        name="Substack",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Substack",
        source_url="https://{username}.substack.com",
        description="Substack newsletter author, publication title, and archive.",
        category="blogging",
        access_type="public_web",
        limitations=["Custom publication domains may not use standard subdomain"],
    )
    url_pattern = "https://{username}.substack.com"
    soft_404_indicators = [
        "Page Not Found",
        "Substack is a publishing network",
        "This Substack does not exist",
    ]


class TumblrUsernameModule(BaseUsernameAdapter):
    """Verifies public blogs on Tumblr."""

    metadata = ModuleMetadata(
        id="username.tumblr",
        name="Tumblr",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Tumblr",
        source_url="https://{username}.tumblr.com",
        description="Tumblr blog existence, title, and public posts.",
        category="social",
        access_type="public_web",
        limitations=["Password-protected or private blogs return 404/redirect"],
    )
    url_pattern = "https://{username}.tumblr.com"
    soft_404_indicators = [
        "There's nothing here.",
        "Whatever you were looking for doesn't exist",
        "404",
    ]


class DisqusUsernameModule(BaseUsernameAdapter):
    """Verifies public commenter profiles on Disqus forum network."""

    metadata = ModuleMetadata(
        id="username.disqus",
        name="Disqus",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Disqus",
        source_url="https://disqus.com/by/{username}/",
        description="Public Disqus commenting profile, bio, and community presence.",
        category="social",
        access_type="public_web",
        limitations=["Private comment history is hidden"],
    )
    url_pattern = "https://disqus.com/by/{username}/"
    soft_404_indicators = ["Page not found", "User not found", "Sorry, this page is not available"]


class ProductHuntUsernameModule(BaseUsernameAdapter):
    """Verifies tech product maker profiles on Product Hunt."""

    metadata = ModuleMetadata(
        id="username.producthunt",
        name="Product Hunt",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Product Hunt",
        source_url="https://www.producthunt.com/@{username}",
        description="Product Hunt maker profile, launched products, and upvotes.",
        category="creator",
        access_type="public_web",
        limitations=["Cloudflare challenges may apply to high-volume requests"],
    )
    url_pattern = "https://www.producthunt.com/@{username}"
    soft_404_indicators = ["Page Not Found", "Oops! We can't find that page", "404"]


class DevpostUsernameModule(BaseUsernameAdapter):
    """Verifies hackathon participant and developer project profiles on Devpost."""

    metadata = ModuleMetadata(
        id="username.devpost",
        name="Devpost",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Devpost",
        source_url="https://devpost.com/{username}",
        description="Devpost hackathon profile, project portfolio, and wins.",
        category="developer",
        access_type="public_web",
        limitations=["User may have hidden project submissions"],
    )
    url_pattern = "https://devpost.com/{username}"
    soft_404_indicators = ["User not found", "Page Not Found", "404 - Not Found"]


class AboutMeUsernameModule(BaseUsernameAdapter):
    """Verifies personal splash pages on About.me."""

    metadata = ModuleMetadata(
        id="username.aboutme",
        name="About.me",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="About.me",
        source_url="https://about.me/{username}",
        description="Personal biography, social links, and identity splash page on About.me.",
        category="social",
        access_type="public_web",
        limitations=["Unclaimed vanity URLs return standard placeholder"],
    )
    url_pattern = "https://about.me/{username}"
    soft_404_indicators = ["Page Not Found", "Couldn't find that page", "claim this domain"]


class LinktreeUsernameModule(BaseUsernameAdapter):
    """Verifies social bio landing pages on Linktree."""

    metadata = ModuleMetadata(
        id="username.linktree",
        name="Linktree",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Linktree",
        source_url="https://linktr.ee/{username}",
        description="Consolidated social profile links on Linktree bio directory.",
        category="creator",
        access_type="public_web",
        limitations=["Suspended or unpublished profiles return 404"],
    )
    url_pattern = "https://linktr.ee/{username}"
    soft_404_indicators = ["The page you are looking for doesn't exist", "Profile Not Found", "404"]


class BuyMeACoffeeUsernameModule(BaseUsernameAdapter):
    """Verifies creator donation and membership pages on Buy Me a Coffee."""

    metadata = ModuleMetadata(
        id="username.buymeacoffee",
        name="Buy Me a Coffee",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Buy Me a Coffee",
        source_url="https://www.buymeacoffee.com/{username}",
        description="Creator support, donation page, and supporter community on Buy Me a Coffee.",
        category="creator",
        access_type="public_web",
        limitations=["Inactive creator accounts return 404"],
    )
    url_pattern = "https://www.buymeacoffee.com/{username}"
    soft_404_indicators = ["Page Not Found", "This page is not available", "404"]


class PatreonUsernameModule(BaseUsernameAdapter):
    """Verifies creator community membership pages on Patreon."""

    metadata = ModuleMetadata(
        id="username.patreon",
        name="Patreon",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Patreon",
        source_url="https://www.patreon.com/{username}",
        description="Public Patreon creator profile, patron count, and membership tiers.",
        category="creator",
        access_type="public_web",
        limitations=["Adult or unlisted creators may be age-gated"],
    )
    url_pattern = "https://www.patreon.com/{username}"
    soft_404_indicators = ["Page Not Found", "This page isn't available", "404"]


class PinterestUsernameModule(BaseUsernameAdapter):
    """Verifies visual discovery and creator profiles on Pinterest."""

    metadata = ModuleMetadata(
        id="username.pinterest",
        name="Pinterest",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Pinterest",
        source_url="https://www.pinterest.com/{username}/",
        description="Pinterest public creator profile, boards, and pins.",
        category="social",
        access_type="public_web",
        limitations=["Login interstitial may appear on repeated lookups"],
    )
    url_pattern = "https://www.pinterest.com/{username}/"
    soft_404_indicators = ["Sorry, we couldn't find that page", "User not found", "404"]


class FlickrUsernameModule(BaseUsernameAdapter):
    """Verifies public photography portfolios on Flickr."""

    metadata = ModuleMetadata(
        id="username.flickr",
        name="Flickr",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Flickr",
        source_url="https://www.flickr.com/people/{username}/",
        description="Public photography portfolio and photographer profile on Flickr.",
        category="creative",
        access_type="public_web",
        limitations=["Photos marked private or friends-only are hidden"],
    )
    url_pattern = "https://www.flickr.com/people/{username}/"
    soft_404_indicators = ["Page Not Found", "This is not the URL you're looking for", "404"]


class VimeoUsernameModule(BaseUsernameAdapter):
    """Verifies video creator and filmmaker channels on Vimeo."""

    metadata = ModuleMetadata(
        id="username.vimeo",
        name="Vimeo",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Vimeo",
        source_url="https://vimeo.com/{username}",
        description="Public filmmaker and video creator channel on Vimeo.",
        category="creative",
        access_type="public_web",
        limitations=["Unlisted channels return 404"],
    )
    url_pattern = "https://vimeo.com/{username}"
    soft_404_indicators = ["Page not found", "Sorry, there is no video here", "404"]


class SoundCloudUsernameModule(BaseUsernameAdapter):
    """Verifies music artist and audio creator profiles on SoundCloud."""

    metadata = ModuleMetadata(
        id="username.soundcloud",
        name="SoundCloud",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="SoundCloud",
        source_url="https://soundcloud.com/{username}",
        description="Public musician, podcast, or audio creator profile on SoundCloud.",
        category="creative",
        access_type="public_web",
        limitations=["Geographic copyright restrictions may restrict certain tracks"],
    )
    url_pattern = "https://soundcloud.com/{username}"
    soft_404_indicators = ["We can't find that user", "User not found", "404"]


class BandcampUsernameModule(BaseUsernameAdapter):
    """Verifies independent musician and artist band pages on Bandcamp."""

    metadata = ModuleMetadata(
        id="username.bandcamp",
        name="Bandcamp",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Bandcamp",
        source_url="https://{username}.bandcamp.com",
        description="Independent musician discography, releases, and merch on Bandcamp.",
        category="creative",
        access_type="public_web",
        limitations=["Fan accounts use different URL structure than artist accounts"],
    )
    url_pattern = "https://{username}.bandcamp.com"
    soft_404_indicators = ["Sorry, that page doesn't exist", "404 Not Found"]


class BehanceUsernameModule(BaseUsernameAdapter):
    """Verifies designer, illustrator, and creative portfolios on Adobe Behance."""

    metadata = ModuleMetadata(
        id="username.behance",
        name="Behance",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Behance",
        source_url="https://www.behance.net/{username}",
        description="Creative design portfolio and project showcase on Adobe Behance.",
        category="creative",
        access_type="public_web",
        limitations=["Mature content warnings may require login"],
    )
    url_pattern = "https://www.behance.net/{username}"
    soft_404_indicators = ["Oops! We can't find that page", "User not found", "404"]


class DribbbleUsernameModule(BaseUsernameAdapter):
    """Verifies digital design shots and portfolio profiles on Dribbble."""

    metadata = ModuleMetadata(
        id="username.dribbble",
        name="Dribbble",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Dribbble",
        source_url="https://dribbble.com/{username}",
        description="Digital designer showcase, portfolio shots, and bio on Dribbble.",
        category="creative",
        access_type="public_web",
        limitations=["Pro-only contact buttons are masked for unauthenticated visitors"],
    )
    url_pattern = "https://dribbble.com/{username}"
    soft_404_indicators = ["Whoops, that page is gone", "User not found", "404"]
