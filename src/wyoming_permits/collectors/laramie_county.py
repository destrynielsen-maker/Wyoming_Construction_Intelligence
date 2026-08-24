from __future__ import annotations

import io
import re
from datetime import date
from urllib.parse import urljoin

import pdfplumber
import requests
from bs4 import BeautifulSoup

from .base import CollectionResult, new_session
from ..models import Permit


ROW_RE = re.compile(
    r"^(?P<number>[A-Z]{1,5}-\d{2}-\d{5})\s+"
    r"(?P<address>.*?)\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})"
    r"(?:\s+\$(?P<valuation>[\d,]+(?:\.\d{2})?))?$"
)
CATEGORY_RE = re.compile(r"^(?P<category>.+?)\s+Permits:\s*\d+\s+Valuations:", re.I)
CATEGORY_BLOCK_RE = re.compile(
    r"(?P<category>[A-Z][A-Z0-9 ()/&-]{3,}?)\s+Permits:\s*\d+\s+Valuations:\s*\$?[\d,]+(?:\.\d{2})?",
    re.I,
)
GLOBAL_ROW_RE = re.compile(
    r"(?P<number>[A-Z]{1,5}-\d{2}-\d{5})\s+"
    r"(?P<address>.*?)\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})"
    r"(?:\s+\$(?P<valuation>[\d,]+(?:\.\d{2})?))?",
    re.I | re.S,
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+\.pdf(?:\?[^)]*)?)\)", re.I)


class LaramieCountyCollector:
    name = "Laramie County"
    freshness_days = 45
    landing_url = "https://www.laramiecountywy.gov/County-Government/County-Departments/Planning-Development"
    source_url = landing_url
    reader_prefix = "https://r.jina.ai/"

    VERIFIED_2026 = (
        "https://www.laramiecountywy.gov/files/assets/public/v/1/january-2026-building-permits-with-valuations.pdf",
        "https://www.laramiecountywy.gov/files/sharedassets/public/v/1/planning/documents/feb-2026-building-permits-with-valuation-by-month.pdf",
        "https://www.laramiecountywy.gov/files/assets/public/v/1/april-building-permits-with-valuation-by-month.pdf",
    )

    def collect(self, session: requests.Session | None = None) -> CollectionResult:
        session = session or new_session()
        urls = self.discover_report_urls(session)
        if not urls:
            raise RuntimeError("No official Laramie County building-permit reports could be discovered")

        permits: dict[str, Permit] = {}
        successful_reports = 0
        reader_reports = 0
        for url in urls:
            parsed, used_reader = self.fetch_and_parse_report(session, url)
            if not parsed:
                continue
            successful_reports += 1
            reader_reports += int(used_reader)
            for permit in parsed:
                permits[permit.key] = permit

        if not successful_reports:
            raise RuntimeError("Official Laramie County permit reports were found but none could be downloaded and parsed")

        values = list(permits.values())
        if not values:
            raise RuntimeError("Laramie County reports parsed with zero permit rows")

        note = f"Official Laramie County monthly Building Permits Issued with Valuations reports ({successful_reports} reports parsed)"
        if reader_reports:
            note += f"; {reader_reports} fetched through read-only text fallback after direct county download failed"
        return CollectionResult(self.name, values, self.landing_url, note)

    def fetch_and_parse_report(self, session: requests.Session, url: str) -> tuple[list[Permit], bool]:
        # First choice is always the official county PDF itself.
        try:
            response = session.get(url, timeout=60)
            if response.ok and self._looks_like_pdf(response):
                parsed = self.parse_pdf(response.content, url)
                if parsed:
                    return parsed, False
        except (requests.RequestException, RuntimeError, ValueError):
            pass

        # Laramie County's CDN intermittently blocks GitHub-hosted runners. Use a
        # read-only text transport as a fallback, then re-validate the county's
        # own report identity before accepting any row. User-facing links remain
        # the official county URLs.
        try:
            response = session.get(
                self.reader_prefix + url,
                headers={"Accept": "text/plain"},
                timeout=90,
            )
            response.raise_for_status()
            if not self._valid_report_identity(response.text):
                return [], True
            return self.parse_text(response.text, url), True
        except (requests.RequestException, RuntimeError, ValueError):
            return [], True

    def discover_report_urls(self, session: requests.Session) -> list[str]:
        year = str(date.today().year)
        discovered: set[str] = set(self.VERIFIED_2026 if year == "2026" else ())

        # Direct official page discovery.
        try:
            response = session.get(
                self.landing_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=45,
            )
            if response.ok:
                soup = BeautifulSoup(response.text, "html.parser")
                for anchor in soup.find_all("a", href=True):
                    text = " ".join(anchor.stripped_strings)
                    href = urljoin(self.landing_url, anchor["href"])
                    hay = f"{text} {href}".lower()
                    if year in hay and "building" in hay and "permit" in hay and "valuation" in hay and ".pdf" in hay:
                        discovered.add(href)
        except requests.RequestException:
            pass

        # If the county page blocks the runner, discover the exact official PDF
        # links from a text rendering of that same official page.
        try:
            response = session.get(self.reader_prefix + self.landing_url, headers={"Accept": "text/plain"}, timeout=90)
            if response.ok:
                for href in MARKDOWN_LINK_RE.findall(response.text):
                    low = href.lower()
                    if year in low and "building" in low and "permit" in low and "valuation" in low:
                        discovered.add(href)
        except requests.RequestException:
            pass

        return sorted(discovered)

    @classmethod
    def parse_pdf(cls, content: bytes, source_url: str) -> list[Permit]:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
        if not cls._valid_report_identity(text):
            raise RuntimeError("Laramie County source identity check failed")
        return cls.parse_text(text, source_url)

    @classmethod
    def parse_text(cls, text: str, source_url: str) -> list[Permit]:
        if not cls._valid_report_identity(text):
            raise RuntimeError("Laramie County source identity check failed")

        # Strip Markdown/table separators while retaining source text. This makes
        # the same parser work with direct PDF extraction and the text fallback.
        clean = text.replace("|", " ")
        clean = re.sub(r"-{3,}", " ", clean)
        clean = re.sub(r"[ \t]+", " ", clean)

        category_matches = list(CATEGORY_BLOCK_RE.finditer(clean))
        permits: dict[str, Permit] = {}

        for idx, category_match in enumerate(category_matches):
            category = " ".join(category_match.group("category").split()).strip()
            start = category_match.end()
            end = category_matches[idx + 1].start() if idx + 1 < len(category_matches) else len(clean)
            segment = clean[start:end]
            for row in GLOBAL_ROW_RE.finditer(segment):
                number = row.group("number").upper()
                address = cls._clean_address(row.group("address"))
                if not address or len(address) > 180:
                    continue
                issued = cls._iso_date(row.group("date"))
                permit = Permit(
                    state="WY",
                    jurisdiction="Laramie County",
                    permit_number=number,
                    issued_date=issued,
                    permit_type=category,
                    project_name=category or None,
                    address=address,
                    valuation=cls._money(row.group("valuation")),
                    source_name="Laramie County Building Permits Issued with Valuations",
                    source_url=source_url,
                    raw={"classification_and_purpose": category, "report_url": source_url},
                )
                permits[permit.key] = permit

        # Direct pdfplumber extraction is usually line-perfect. If category block
        # formatting changed, preserve the simpler line parser as a safe fallback.
        if not permits:
            category = ""
            for raw_line in clean.splitlines():
                line = " ".join(raw_line.split()).strip()
                category_match = CATEGORY_RE.match(line)
                if category_match:
                    category = category_match.group("category").strip()
                    continue
                row = ROW_RE.match(line)
                if not row:
                    continue
                permit = Permit(
                    state="WY",
                    jurisdiction="Laramie County",
                    permit_number=row.group("number").upper(),
                    issued_date=cls._iso_date(row.group("date")),
                    permit_type=category,
                    project_name=category or None,
                    address=cls._clean_address(row.group("address")),
                    valuation=cls._money(row.group("valuation")),
                    source_name="Laramie County Building Permits Issued with Valuations",
                    source_url=source_url,
                    raw={"classification_and_purpose": category, "report_url": source_url},
                )
                permits[permit.key] = permit

        return list(permits.values())

    @staticmethod
    def _clean_address(value: str) -> str:
        value = re.sub(r"\s+", " ", value or "").strip(" -:;,")
        # Text renderers sometimes repeat the category total immediately before a
        # permit row; discard that harmless numeric prefix if present.
        value = re.sub(r"^\d+\s+\$[\d,]+(?:\.\d{2})?\s+", "", value)
        return value.strip()

    @staticmethod
    def _looks_like_pdf(response: requests.Response) -> bool:
        return "pdf" in (response.headers.get("content-type") or "").lower() or response.content.startswith(b"%PDF")

    @staticmethod
    def _valid_report_identity(text: str) -> bool:
        normalized = " ".join((text or "").split()).lower()
        return "laramie county planning & development office" in normalized and "building permits issued with valuations" in normalized

    @staticmethod
    def _iso_date(value: str) -> str:
        month, day, year = (int(part) for part in value.split("/"))
        return date(year, month, day).isoformat()

    @staticmethod
    def _money(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
