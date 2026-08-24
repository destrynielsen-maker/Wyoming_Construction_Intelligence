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

MARKDOWN_TEXT = """Title: Laramie County Planning & Development Office

Laramie County Planning & Development Office
3966 Archer PKWY Cheyenne, WY 82009

Building Permits Issued with Valuations

COMMERCIAL NEW CONSTRUCTION | Permits: | 2 | Valuations: | $675,000.00
BP-26-00202 | 2680 ROAD 238 | 04/23/2026 | $275,000.00
BP-26-00343 | 9501 Happy Jack Rd | 04/27/2026 | $400,000.00
RESIDENTIAL NEW SINGLE FAMILY | Permits: | 1 | Valuations: | $425,000.00
BP-26-00350 | 1234 PRAIRIE VIEW RD | 04/28/2026 | $425,000.00
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

    def test_parse_plain_text(self):
        records = LaramieCountyCollector.parse_text(REPORT_TEXT, "https://example.test/january.pdf")
        by_number = {p.permit_number: p for p in records}
        self.assertEqual(len(by_number), 4)
        self.assertEqual(by_number["BP-26-00018"].permit_type, "COMMERCIAL NEW CONSTRUCTION")
        self.assertEqual(by_number["BP-25-01341"].address, "4113 DEREK CT")
        self.assertEqual(by_number["BP-25-01340"].valuation, 136095.0)

    def test_parse_markdown_table_text(self):
        records = LaramieCountyCollector.parse_text(MARKDOWN_TEXT, "https://example.test/april.pdf")
        by_number = {p.permit_number: p for p in records}
        self.assertEqual(len(by_number), 3)
        self.assertEqual(by_number["BP-26-00343"].address, "9501 Happy Jack Rd")
        self.assertEqual(by_number["BP-26-00343"].valuation, 400000.0)
        self.assertEqual(by_number["BP-26-00350"].permit_type, "RESIDENTIAL NEW SINGLE FAMILY")

if __name__ == "__main__":
    unittest.main()
