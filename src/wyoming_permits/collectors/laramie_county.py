from __future__ import annotations

import io
import re
from calendar import month_name
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


class LaramieCountyCollector:
    name = "Laramie County"
    freshness_days = 45
    landing_url = "https://www.laramiecountywy.gov/County-Government/County-Departments/Planning-Development"
    source_url = landing_url

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
        for url in urls:
            try:
                response = session.get(url, timeout=60)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                if not self._looks_like_pdf(response):
                    continue
                parsed = self.parse_pdf(response.content, url)
                if not parsed:
                    continue
                successful_reports += 1
                for permit in parsed:
                    permits[permit.key] = permit
            except requests.RequestException:
                continue
        if not successful_reports:
            raise RuntimeError("Official Laramie County permit reports were found but none could be downloaded and parsed")
        values = list(permits.values())
        if not values:
            raise RuntimeError("Laramie County reports parsed with zero permit rows")
        return CollectionResult(self.name, values, self.landing_url, f"Official Laramie County monthly Building Permits Issued with Valuations reports ({successful_reports} reports parsed)")

    def discover_report_urls(self, session: requests.Session) -> list[str]:
        year = str(date.today().year)
        discovered: set[str] = set(self.VERIFIED_2026 if year == "2026" else ())
        try:
            response = session.get(self.landing_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}, timeout=45)
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
        today = date.today()
        recent_months = []
        for offset in range(0, 5):
            month = today.month - offset
            yr = today.year
            while month <= 0:
                month += 12
                yr -= 1
            if yr == today.year:
                recent_months.append((yr, month))
        for yr, month in recent_months:
            full = month_name[month].lower()
            abbr = full[:3]
            candidates = (
                f"https://www.laramiecountywy.gov/files/assets/public/v/1/{full}-{yr}-building-permits-with-valuations.pdf",
                f"https://www.laramiecountywy.gov/files/assets/public/v/1/{full}-building-permits-with-valuation-by-month.pdf",
                f"https://www.laramiecountywy.gov/files/sharedassets/public/v/1/planning/documents/{abbr}-{yr}-building-permits-with-valuation-by-month.pdf",
                f"https://www.laramiecountywy.gov/files/sharedassets/public/v/1/planning/documents/building/building-permits-with-valuation-by-month-{full}-{yr}.pdf",
            )
            for candidate in candidates:
                try:
                    r = session.get(candidate, timeout=30)
                    if r.ok and self._looks_like_pdf(r) and self._valid_report_identity(self._first_page_text(r.content)):
                        discovered.add(candidate)
                        break
                except requests.RequestException:
                    continue
        return sorted(discovered)

    @classmethod
    def parse_pdf(cls, content: bytes, source_url: str) -> list[Permit]:
        permits: list[Permit] = []
        category = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            identity_checked = False
            for page in pdf.pages:
                text = page.extract_text() or ""
                if not identity_checked:
                    if not cls._valid_report_identity(text):
                        raise RuntimeError("Laramie County source identity check failed")
                    identity_checked = True
                for raw_line in text.splitlines():
                    line = " ".join(raw_line.split()).strip()
                    if not line:
                        continue
                    category_match = CATEGORY_RE.match(line)
                    if category_match:
                        category = category_match.group("category").strip()
                        continue
                    row = ROW_RE.match(line)
                    if not row:
                        continue
                    permits.append(Permit(state="WY", jurisdiction="Laramie County", permit_number=row.group("number"), issued_date=cls._iso_date(row.group("date")), permit_type=category, project_name=category or None, address=row.group("address").strip(), valuation=cls._money(row.group("valuation")), source_name="Laramie County Building Permits Issued with Valuations", source_url=source_url, raw={"classification_and_purpose": category, "report_url": source_url}))
        return permits

    @staticmethod
    def _looks_like_pdf(response: requests.Response) -> bool:
        return "pdf" in (response.headers.get("content-type") or "").lower() or response.content.startswith(b"%PDF")

    @staticmethod
    def _first_page_text(content: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return (pdf.pages[0].extract_text() or "") if pdf.pages else ""
        except Exception:
            return ""

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
