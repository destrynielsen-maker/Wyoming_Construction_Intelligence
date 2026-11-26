"""An additive manifest; no effect on collector, lead, or feed eligibility."""
from datetime import datetime


def _known_success(value):
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value).tzinfo is not None
    except ValueError:
        return False


def laramie_row(status, baseline, kept, observed, prior_success):
    """Use identity sets, not subtraction of counts; absent inputs are unknown."""
    successful = observed is not None
    return {
        "id": "wy-laramie-county", "label": "Laramie County", "mode": "automatic",
        "coverage": "Laramie County only; issued building permit reports",
        "last_attempt_at": status.get("last_attempt_at"),
        "last_success_at": status.get("last_success_at"),
        "latest_authoritative_date": status.get("newest_permit_date"),
        "latest_date_kind": "issued" if status.get("newest_permit_date") else None,
        "source_age_days": status.get("days_since_newest_permit"),
        "new_since_previous_success": (
            len(observed - baseline) if successful and baseline is not None and _known_success(prior_success) else None
        ),
        "retained_records": len(kept) if kept is not None else None,
        "observed_records": len(observed) if successful else None,
        "availability": "reachable" if successful else "unavailable",
        "freshness_status": status.get("freshness_status"),
        "collection_outcome": ("success" if observed else "no_data") if successful else "error",
    }


def manual_research_row(ident, label, coverage):
    return {
        "id": ident, "label": label, "mode": "manual",
        "coverage": coverage,
        "last_attempt_at": None, "last_success_at": None,
        "latest_authoritative_date": None, "latest_date_kind": None,
        "source_age_days": None, "new_since_previous_success": None,
        "retained_records": None, "observed_records": None,
        "availability": "not_attempted", "collection_outcome": "manual_only",
    }


def manifest(rows, generated_at):
    return {
        "schema_version": 1, "generated_at": generated_at,
        "sources": [*rows,
            manual_research_row("wy-jackson-town", "Town of Jackson",
                                "Manual PDF preview only; not collected or published"),
            manual_research_row("wy-teton-county", "Unincorporated Teton County",
                                "Application preview only; no verified issued feed or published coverage"),
        ],
    }
