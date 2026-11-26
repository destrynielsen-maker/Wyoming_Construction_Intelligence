"""Opt-in Town of Jackson public-issued-report preview. Read local PDFs, print JSON."""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import subprocess

REPORTS = "https://twn-jackson-wy.smartgovcommunity.com/Public/ReportsView"
JURISDICTION = "Town of Jackson"
MAX_BYTES = 100_000_000
MAX_PAGES = 12
DAY = r"\d{1,2}/\d{1,2}/\d{4}"
WINDOW = re.compile(rf"ALL PERMIT TYPES SUBMITTED OR ISSUED BETWEEN\s*({DAY}) AND ({DAY})")
ROW = re.compile(r"^(.*?)([A-Z]+\d{2}-\d{2,7})\s+Submitted:")
ISSUED = re.compile(rf"\s{{2,}}Issued:\s*({DAY})?\s*$")
DEPARTMENT = re.compile(r"^(BUILDING|ENGINEERING/P|PLANNING)\b")
# Public report geometry wraps the case type but has a separate project column.
TYPES = {
    "B-ADDENDUM", "B-MECHANICAL", "B-PLUMBING", "B-RESIDENTIAL ADDITION",
    "B-RESIDENTIAL ALTERATION/REPAIR", "B-RESIDENTIAL NEW CONSTRUCTION",
    "B-COMMERCIAL ADDITION", "B-COMMERCIAL NEW CONSTRUCTION",
    "B-COMMERCIAL ALTERATION/REPAIR",
}


def report_date(value):
    return datetime.strptime(value, "%m/%d/%Y").date()


def report_rows(text, start, end):
    if not timedelta(0) <= end-start <= timedelta(days=6):
        raise ValueError("Only one window of up to seven days may be replayed per PDF")
    if not 1 <= len(text.split("\f")) - 1 <= MAX_PAGES:
        raise ValueError("Unexpected Town report page count")
    windows = {(report_date(a), report_date(b)) for a,b in WINDOW.findall(text)}
    if windows != {(start, end)} or "Issued Permits By Department" not in text:
        raise ValueError("Report title or window mismatch")
    _, details = text.split("Issued Permit Details", 1)
    lines = details.splitlines()
    starts = [i for i, line in enumerate(lines) if "Submitted:" in line]
    if not starts:
        raise ValueError("No recognizable detail section")
    department = case_type = None
    for i, after in zip(starts, starts[1:]+[len(lines)]):
        match = ROW.match(lines[i])
        if not match:
            raise ValueError("Unrecognized permit detail row")
        prefix, ident = match.groups()
        dept = DEPARTMENT.match(prefix)
        if dept:
            department = dept.group(1)
            case_type = None
        if department != "BUILDING":
            continue
        prefix = prefix[dept.end():] if dept else prefix
        first = prefix.strip()
        if first:
            col = len(match.group(1).rstrip())-len(first)
            continuation = [row[col:match.start(2)].strip() for row in lines[i+1:min(i+5, after)]]
            label = first
            for item in continuation:
                if item:
                    label += " " + item
            label = label.replace("B- ", "B-").replace("CONSTRUCTIO N", "CONSTRUCTION")
            label = re.sub(r"ALTERATION/(?:R E|RE )PAIR|ALTERATION/R EPAIR", "ALTERATION/REPAIR", label)
            case_type = label if label in TYPES else "unknown_building_type"
        if not case_type:
            raise ValueError("Missing building permit type")
        dates = [m.group(1) for line in lines[i+1:after] if (m := ISSUED.search(line))]
        if len(dates) != 1:
            raise ValueError("Missing or ambiguous explicit issue-date field")
        issued = report_date(dates[0]) if dates[0] else None
        raw_project_text = " ".join(row[match.start(2):] for row in lines[i+1:min(i+5,after)])
        explicit_sf = bool(re.search(r"\bNEW\s+(?:SF\s+HOME|SINGLE[- ]FAMILY(?:\s+(?:HOME|RESIDENCE))?)\b",
                                     raw_project_text, re.I))
        yield ident, case_type, issued, explicit_sf


def summarize(text, start, end):
    all_rows = list(report_rows(text,start,end))
    if not all_rows:
        raise ValueError("No Town Building Department rows")
    health = Counter()
    permit_ids, issued_ids = {r[0] for r in all_rows}, {}
    for ident, kind, issued, explicit_sf in all_rows:
        if not issued:
            health["missing_issued_date_rows"] += 1
        elif not start <= issued <= end:
            health["out_of_window_issue_rows"] += 1
        else:
            evidence = kind, issued, explicit_sf
            prior = issued_ids.setdefault(ident,evidence)
            if prior != evidence:
                raise ValueError(f"Conflicting issuance cycles for {ident}")
            health["in_window_issue_rows"] += 1
    candidates = [
        {"permit_number": ident, "issued_date": issued.isoformat(),
         "jurisdiction": JURISDICTION, "source_type": kind,
         "contractor": None, "qualification": "manual_review_only"}
        for ident,(kind,issued,sf) in sorted(issued_ids.items())
        if (kind == "B-RESIDENTIAL NEW CONSTRUCTION" and sf)
        or kind == "B-COMMERCIAL NEW CONSTRUCTION"
    ]
    return {
        "jurisdiction": JURISDICTION, "source": REPORTS, "production_writes": 0,
        "start": start.isoformat(), "end": end.isoformat(),
        "building_detail_rows": len(all_rows), "distinct_building_ids": len(permit_ids),
        "distinct_in_window_issued_ids": len(issued_ids),
        "latest_in_window_issue": max((ev[1].isoformat() for ev in issued_ids.values()), default=None),
        "issued_type_counts": dict(sorted(Counter(ev[0] for ev in issued_ids.values()).items())),
        "repeated_in_window_cycles_removed": health["in_window_issue_rows"]-len(issued_ids),
        "new_leads_promoted": 0, "candidates": candidates, **health,
    }


def read_pdf(path):
    with path.open("rb") as fd:
        if fd.read(5) != b"%PDF-" or not 1 <= path.stat().st_size <= MAX_BYTES:
            raise ValueError("Town report is not a bounded PDF")
    result = subprocess.run(
        ["pdftotext", "-layout", "-f", "1", "-l", str(MAX_PAGES+1), str(path.resolve()), "-"],
        capture_output=True, check=True, timeout=25,
    )
    if len(result.stdout) > 500_000:
        raise ValueError("Town report text exceeds bound")
    return result.stdout.decode("utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pdf", type=Path)
    p.add_argument("--start", type=date.fromisoformat, required=True)
    p.add_argument("--end", type=date.fromisoformat, required=True)
    args = p.parse_args()
    print(json.dumps(summarize(read_pdf(args.pdf), args.start, args.end), indent=2))


if __name__ == "__main__":
    main()
