from datetime import date
import unittest
from unittest.mock import patch

from wyoming_permits import teton_application_preview as preview

INDEX = """
<h1>Building Permit Activity Reports</h1>
<a href="Archive.aspx?ADID=782">August 2026</a>
<a href="https://wrong.example/Archive.aspx?ADID=3">December 2026</a>
<a href="/Archive.aspx?ADID=781">July 2026</a>
<a href="/Archive.aspx?ADID=999">Test report</a>
"""
HEADING = "PERMIT NUMBER PROJECT DESCRIPTION DATE SUBMITTED SITE ADDRESS OWNER"
ROW = "BDR2026-0119 New single-family residence. 08/10/2026 $ 7,500,000.00 SAMPLE OWNER"


class TetonPreviewTest(unittest.TestCase):
    def test_only_sorted_official_months(self):
        self.assertEqual([month for month, _ in preview.discover(INDEX)], ["2026-08", "2026-07"])

    def test_application_is_not_issued_and_owner_not_contractor(self):
        row, = preview.parse_text(f"{HEADING}\n{ROW}\n{ROW}", "2026-08", "public")
        self.assertEqual(row["application_id"], "BDR2026-0119")
        self.assertEqual(row["submitted_date"], "2026-08-10")
        self.assertIsNone(row["issued_date"])
        self.assertIsNone(row["contractor"])
        self.assertNotIn("SAMPLE OWNER", repr(row))

    def test_reject_issued_or_wrong_month_or_ambiguous(self):
        for h, r in [
            (HEADING.replace("SUBMITTED", "ISSUED"), ROW),
            (HEADING, ROW.replace("08/10", "07/10")),
            (HEADING, ROW.replace("08/10/2026", "08/01/2026 08/10/2026")),
            (HEADING, "Unrecognized layout"),
        ]:
            with self.subTest(h=h, r=r), self.assertRaises(ValueError):
                preview.parse_text(f"{h}\n{r}", "2026-08", "public")

    def test_stale_preview_and_conflicts(self):
        def that_pdf(_payload, month, url):
            row = ROW if month == "2026-08" else ROW.replace("08/10", "07/10")
            return preview.parse_text(f"{HEADING}\n{row}", month, url)
        with patch.object(preview, "parse_pdf", side_effect=that_pdf):
            result = preview.run(1, fetch=lambda _: INDEX, today=date(2026, 11, 26))
            self.assertEqual(result["applications"], 1)
            self.assertEqual(result["freshness_status"], "stale")
            self.assertIsNone(result["issued_permits"])
            self.assertIsNone(result["contractor_coverage"])
            with self.assertRaisesRegex(ValueError, "conflicting dates"):
                preview.run(2, fetch=lambda _: INDEX, today=date(2026, 11, 26))

    def test_html_is_not_pdf(self):
        with self.assertRaisesRegex(ValueError, "Not a PDF"):
            preview.parse_pdf(b"<html>access error</html>", "2026-08", "public")


if __name__ == "__main__":
    unittest.main()
