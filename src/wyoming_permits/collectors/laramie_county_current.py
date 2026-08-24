from __future__ import annotations

import html
import re
from datetime import date
from urllib.parse import urljoin

import requests

from .laramie_county import LaramieCountyCollector


# Jina/read-only renderers may preserve a site's relative href instead of
# normalizing it to an absolute URL. Accept both forms and resolve them against
# the official Laramie County landing page before returning a source URL.
READER_LINK_RE = re.compile(
    r"\[(?P<label>[^\]]+)\]\((?P<href><[^>]+>|[^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)",
    re.I,
)


def current_year_report_links(
    markdown: str,
    year: int | None = None,
    base_url: str = LaramieCountyCollector.landing_url,
) -> list[str]:
    wanted_year = str(year or date.today().year)
    discovered: set[str] = set()
    for match in READER_LINK_RE.finditer(markdown or ""):
        label = html.unescape(match.group("label"))
        raw_href = html.unescape(match.group("href")).strip("<>")
        href = urljoin(base_url, raw_href)
        hay = f"{label} {href}".lower()
        if (
            wanted_year in hay
            and "building" in hay
            and "permit" in hay
            and "valuation" in hay
            and ".pdf" in href.lower()
            and "laramiecountywy.gov" in href.lower()
        ):
            discovered.add(href)
    return sorted(discovered)


class LaramieCountyCurrentCollector(LaramieCountyCollector):
    """Discover all current-year official Laramie County permit reports.

    The county consistently identifies the year in the human-readable link
    label, while some PDF filenames omit the year and some renderers preserve
    relative hrefs. The base collector remains responsible for source identity
    validation and permit parsing.
    """

    def discover_report_urls(self, session: requests.Session) -> list[str]:
        discovered = set(super().discover_report_urls(session))
        try:
            response = session.get(
                self.reader_prefix + self.landing_url,
                headers={"Accept": "text/plain"},
                timeout=90,
            )
            if response.ok:
                discovered.update(
                    current_year_report_links(
                        response.text,
                        base_url=self.landing_url,
                    )
                )
        except requests.RequestException:
            pass
        return sorted(discovered)
