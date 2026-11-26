from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import json

from wyoming_permits.collectors.base import CollectionResult
from wyoming_permits.models import Permit
from wyoming_permits.pipeline import run
from wyoming_permits.storage import load_permits


class Frozen:
    name = "Laramie County"
    freshness_days = 45
    source_url = "https://example.invalid/reports"

    def __init__(self, ids):
        self.ids = ids

    def collect(self):
        if self.ids is None:
            raise RuntimeError("source failure fixture")
        rows = [Permit(state="WY", jurisdiction=self.name, permit_number=i,
                       issued_date="2026-11-22", permit_type="New Single Family",
                       address="synthetic", source_url=self.source_url) for i in self.ids]
        return CollectionResult(self.name, rows, self.source_url)


def replay(root, ids):
    with patch("wyoming_permits.pipeline.COLLECTORS", [Frozen(ids)]):
        result = run(root)
    payload = json.loads((root/"public/data/sources.json").read_text())
    assert payload["sources"] == result["sources"]
    assert payload["reporting_v1"]["generated_at"] == payload["generated_at"]
    return payload["reporting_v1"]["sources"]


class ReportingTests(TestCase):
    def test_prior_identity_not_subtraction_and_failure_preserves_reference(self):
        with TemporaryDirectory() as work:
            root = Path(work)
            a, town, county = replay(root, ["a", "b"])
            self.assertIsNone(a["new_since_previous_success"])
            self.assertEqual((a["retained_records"], a["observed_records"]), (2, 2))
            self.assertEqual((town["mode"], town["availability"], town["collection_outcome"]),
                             ("manual", "not_attempted", "manual_only"))
            self.assertIsNone(town["retained_records"])
            self.assertIsNone(county["latest_authoritative_date"])
            failed, *_ = replay(root, None)
            self.assertEqual(failed["last_success_at"], a["last_success_at"])
            self.assertIsNone(failed["observed_records"])
            self.assertIsNone(failed["new_since_previous_success"])
            self.assertEqual((failed["collection_outcome"], failed["retained_records"]), ("error", 2))
            recovered, *_ = replay(root, ["b", "c", "c"])
            self.assertEqual((recovered["new_since_previous_success"], recovered["retained_records"],
                              recovered["observed_records"]), (1, 3, 2))
            self.assertEqual(len(load_permits(root/"data/permits.json")), 3)
