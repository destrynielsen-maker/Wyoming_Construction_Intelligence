from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from wyoming_permits.jackson_town_issued_preview import read_pdf, summarize

START, END = date(2026,11,16), date(2026,11,22)
HEADER = '''Issued Permits By Department
ALL PERMIT TYPES SUBMITTED OR ISSUED BETWEEN
11/16/2026 AND 11/22/2026
Issued Permit Details
'''
SF = '''BUILDING     B-          B26-0999                  Submitted: 07/13/2026
DEPARTMENT   RESIDENTIAL                       Technically Complete: 07/13/2026
             NEW         Synthetic New SF Home       Approved: 11/10/2026
             CONSTRUCTIO                          Ready to Issue: 11/10/2026
             N                                            Issued: 11/17/2026
'''
CONTINUED = '''                         B26-0999                  Submitted: 07/13/2026
                         Synthetic New SF Home       Approved: 11/10/2026
                                                          Issued: 11/17/2026
'''
PLUMBING = '''             B-PLUMBING  PLUMB26-0087              Submitted: 11/16/2026
                         Synthetic MF home                   Issued: 11/16/2026
'''


class JacksonTownPreviewTests(unittest.TestCase):
    def run_report(self, details):
        return summarize(HEADER+details+"\f", START, END)

    def test_cycles_dedup_and_no_gc_or_address_guess(self):
        result = self.run_report(SF+CONTINUED+PLUMBING)
        self.assertEqual(result["distinct_in_window_issued_ids"], 2)
        self.assertEqual(result["repeated_in_window_cycles_removed"], 1)
        candidate, = result["candidates"]
        self.assertEqual((candidate["permit_number"],candidate["issued_date"]),
                         ("B26-0999","2026-11-17"))
        self.assertIsNone(candidate["contractor"])
        self.assertNotIn("Synthetic", repr(result))
        self.assertEqual(result["new_leads_promoted"], 0)

    def test_missing_and_out_of_range_are_not_issued(self):
        details = SF.replace("Issued: 11/17/2026","Issued:") + PLUMBING.replace(
            "Issued: 11/16/2026", "Issued: 11/25/2026")
        result = self.run_report(details)
        self.assertEqual(result["distinct_in_window_issued_ids"],0)
        self.assertEqual((result["missing_issued_date_rows"],result["out_of_window_issue_rows"]),(1,1))

    def test_conflicting_cycle_and_wrong_window_rejected(self):
        with self.assertRaisesRegex(ValueError,"Conflicting issuance"):
            self.run_report(SF+CONTINUED.replace("Issued: 11/17/2026","Issued: 11/18/2026"))
        with self.assertRaisesRegex(ValueError,"window mismatch"):
            summarize(HEADER+SF+"\f",START,date(2026,11,20))

    def test_reject_non_pdf(self):
        with TemporaryDirectory() as d:
            f = Path(d)/"report.pdf"
            f.write_bytes(b'<html>not a report</html>')
            with self.assertRaisesRegex(ValueError,"bounded PDF"):
                read_pdf(f)


if __name__ == "__main__":
    unittest.main()
