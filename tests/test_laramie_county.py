import unittest
from wyoming_permits.collectors.laramie_county import LaramieCountyCollector

REPORT_TEXT = """Laramie County Planning & Development Office
3966 Archer PKWY Cheyenne, WY 82009
Building Permits Issued with Valuations
Organized by Classification and Purpose. Additional details available on our website
Permits Issued 01/01/2026 - 01/31/2026
Permit Number Site Address Date Issued Valuations
COMMERCIAL NEW CONSTRUCTION Permits: 2 Valuations: $379,000.00
2 $379,000.00
BP-26-00009 120 US 85 01/13/2026 $4,000.00
BP-26-00018 90 ROAD 161 01/13/2026 $375,000.00
RESIDENTIAL NEW SINGLE FAMILY Permits: 2 Valuations: $239,455.00
2 $239,455.00
BP-25-01340 1222 SOUTH CAROLINA RD 01/06/2026 $136,095.00
BP-25-01341 4113 DEREK CT 01/06/2026 $103,360.00
"""

class LaramieCountyTests(unittest.TestCase):
    def test_identity_guard(self):
        self.assertTrue(LaramieCountyCollector._valid_report_identity(REPORT_TEXT))
        self.assertFalse(LaramieCountyCollector._valid_report_identity("Hilton Head Island permit report"))
    def test_row_regex(self):
        from wyoming_permits.collectors.laramie_county import ROW_RE
        m = ROW_RE.match("BP-26-00018 90 ROAD 161 01/13/2026 $375,000.00")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("number"), "BP-26-00018")
        self.assertEqual(m.group("address"), "90 ROAD 161")
        self.assertEqual(LaramieCountyCollector._money(m.group("valuation")), 375000.0)
    def test_category_regex(self):
        from wyoming_permits.collectors.laramie_county import CATEGORY_RE
        m = CATEGORY_RE.match("RESIDENTIAL NEW SINGLE FAMILY Permits: 8 Valuations: $1,450,045.00")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("category"), "RESIDENTIAL NEW SINGLE FAMILY")

if __name__ == "__main__":
    unittest.main()
