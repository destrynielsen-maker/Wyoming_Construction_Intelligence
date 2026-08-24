from __future__ import annotations

import re
from datetime import date

import requests

from .laramie_county import LaramieCountyCollector


READER_LINK_RE = re.compile(
    r"\[(?P<label>[^\]]+)\]\((?P<href>https?://[^)]+\.pdf(?:\?[^)]*)?)\)",
    re.I,
)


def current_year_report_links(markdown: str, year: int | None = None) -> list[str]:
    wanted_year = str(year or date.today().year)
    discovered: set[str] = set()
    for match in READER_LINK_RE.finditer(markdown or ""):
        label = match.group("label")
        href = match.group("href")
        hay = f"{label} {href}".lower()
        if (
            wanted_year in hay
            and "building" in hay
            and "permit" in hay
            and "valuation" in hay
        ):
            discovered.add(href)
    return sorted(discovered)


class LaramieCountyCurrentCollector(LaramieCountyCollector):
    """Extend report discovery to use the official link label as well as URL.

    Laramie County's current report links consistently identify the year in the
    human-readable link label, while some PDF filenames omit the year. The base
    collector remains responsible for source identity validation and parsing.
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
                discovered.update(current_year_report_links(response.text))
        except requests.RequestException:
            pass
        return sorted(discovered)
