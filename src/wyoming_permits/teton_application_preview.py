"""Read-only Teton County public application preview; never enters the issued-permit store."""
import argparse
from calendar import month_name
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
import json
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
import pdfplumber
import requests

INDEX = "https://www.tetoncountywy.gov/Archive.aspx?AMID=55"
HOST = urlsplit(INDEX).netloc
MONTHS = {name: i for i, name in enumerate(month_name) if i}
MONTH = re.compile(rf"({'|'.join(MONTHS)}) (20[0-9]{{2}})")
ID_START = re.compile(r"^\s*([A-Z]{2,5}20\d{2}-\d{1,7})\b")
SUBMITTED = re.compile(r"\b(\d{1,2}/\d{1,2}/20\d{2})\b")
MAX_BYTES = 10 * 1024 * 1024


def get_public(url):
    dest = urlsplit(url)
    if (dest.scheme, dest.netloc) != ("https", HOST) or dest.path != "/Archive.aspx":
        raise ValueError("Not an official County archive input URL")
    # CivicEngage redirects its public ADID links to public PDF items. Restrict the
    # single follow-up to that same host and the same numeric item.
    response = requests.get(url, timeout=(8, 20), stream=True, allow_redirects=False)
    if response.is_redirect:
        location = urljoin(url, response.headers.get("Location", ""))
        target = urlsplit(location)
        item = re.fullmatch(r"ADID=(\d+)", dest.query)
        response.close()
        if not item or (target.scheme, target.netloc, target.path, target.query, target.fragment) != (
            "https", HOST, f"/ArchiveCenter/ViewFile/Item/{item[1]}", "", ""
        ):
            raise ValueError("Unexpected archive redirect")
        response = requests.get(location, timeout=(8, 20), stream=True, allow_redirects=False)
    with response:
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Archive endpoint did not return HTTP 200")
        result = bytearray()
        for chunk in response.iter_content(65_536):
            result.extend(chunk)
            if len(result) > MAX_BYTES:
                raise ValueError("Archive response exceeded safety limit")
    return bytes(result)


def discover(html):
    soup = BeautifulSoup(html, "html.parser")
    if "Building Permit Activity Reports" not in soup.get_text(" ", strip=True):
        raise ValueError("Missing official archive category")
    reports = {}
    for anchor in soup.find_all("a", href=True):
        label = MONTH.fullmatch(anchor.get_text(" ", strip=True))
        ref = re.fullmatch(r"(?:/)?Archive\.aspx\?ADID=(\d+)", anchor["href"], re.I)
        if not label or not ref:
            continue
        month = f"{label[2]}-{MONTHS[label[1]]:02d}"
        url = urljoin(INDEX, f"/Archive.aspx?ADID={ref[1]}")
        if month in reports and reports[month] != url:
            raise ValueError(f"Multiple different links for {month}")
        reports[month] = url
    if not reports:
        raise ValueError("No official monthly report links")
    return sorted(reports.items(), reverse=True)


def parse_text(text, period, url):
    lines = text.splitlines()
    header = " ".join(" ".join(lines[:10]).upper().split())
    if not all(column in header for column in ("DATE SUBMITTED", "PERMIT NUMBER", "PROJECT DESCRIPTION", "SITE ADDRESS", "OWNER")):
        raise ValueError("Unexpected County application report heading")
    records = {}
    for line in lines:
        ident = ID_START.match(line)
        if not ident:
            continue
        suffix = line[ident.end():].split("$", 1)[0]
        matches = SUBMITTED.findall(suffix)
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous submission date for {ident[1]}")
        submitted = datetime.strptime(matches[0], "%m/%d/%Y").date().isoformat()
        if submitted[:7] != period:
            raise ValueError(f"Submission does not match monthly report: {ident[1]}")
        row = {"jurisdiction": "Teton County, WY", "application_id": ident[1], "stage": "application_submitted",
               "submitted_date": submitted, "issued_date": None, "contractor": None, "source_url": url}
        if ident[1] in records and records[ident[1]] != row:
            raise ValueError(f"Conflicting rows: {ident[1]}")
        records[ident[1]] = row
    if not records:
        raise ValueError("No application rows; refuse to interpret unknown layout as empty coverage")
    return list(records.values())


def parse_pdf(payload, month, url):
    if not payload.startswith(b"%PDF-"):
        raise ValueError("Not a PDF; possible replacement/error page")
    with pdfplumber.open(BytesIO(payload)) as document:
        if not 1 <= len(document.pages) <= 30:
            raise ValueError("Unexpected report page count")
        text = "\n".join(page.extract_text(layout=True) or "" for page in document.pages)
    return parse_text(text, month, url)


def run(months=1, *, fetch=get_public, today=None):
    if not 1 <= months <= 6:
        raise ValueError("months must be between 1 and 6")
    today = today or datetime.now(timezone.utc).date()
    records = {}
    report_meta = []
    for month, url in discover(fetch(INDEX))[:months]:
        rows = parse_pdf(fetch(url), month, url)
        for row in rows:
            ident = row["application_id"]
            if ident in records and records[ident]["submitted_date"] != row["submitted_date"]:
                raise ValueError(f"An application ID was reused with conflicting dates: {ident}")
            records.setdefault(ident, row)
        report_meta.append({"month": month, "url": url, "unique_applications": len(rows)})
    ordered = sorted(records.values(), key=lambda row: (row["submitted_date"], row["application_id"]), reverse=True)
    newest = ordered[0]["submitted_date"]
    age = (today - date.fromisoformat(newest)).days
    if age < 0:
        raise ValueError("Unexpected future submission date")
    return {
        "dataset": "public_application_preview",
        "freshness_status": "stale" if age > 60 else "fresh",
        "newest_submitted_date": newest,
        "days_since_newest_submission": age,
        "applications": len(ordered),
        "issued_permits": None,
        "contractor_coverage": None,
        "reports": report_meta,
        "records": ordered,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, choices=range(1, 7), default=1)
    parser.add_argument("--summary", action="store_true", help="Omit record-level application rows.")
    parser.add_argument("--index-file", type=Path, help="Previously downloaded official archive HTML.")
    parser.add_argument("--report-dir", type=Path, help="Previously downloaded PDFs named by numeric ADID.")
    args = parser.parse_args()
    if bool(args.index_file) != bool(args.report_dir):
        parser.error("--index-file and --report-dir must be used together")
    def from_files(url):
        if url == INDEX:
            path = args.index_file
        else:
            ref = re.fullmatch(r"ADID=(\d+)", urlsplit(url).query)
            path = args.report_dir / (ref[1] + ".pdf")
        with path.open("rb") as handle:
            payload = handle.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("Archive input exceeded safety limit")
        return payload
    result = run(args.months, fetch=from_files if args.index_file else get_public)
    if args.summary:
        del result["records"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
