import unittest

from wyoming_permits.collectors.laramie_county_current import current_year_report_links


BASE = "https://www.laramiecountywy.gov/County-Government/County-Departments/Planning-Development"


class LaramieCurrentDiscoveryTests(unittest.TestCase):
    def test_year_can_come_from_link_label(self):
        markdown = """
[April 2026 Building Permits with Valuations](https://www.laramiecountywy.gov/files/assets/public/v/1/april-building-permits-with-valuation-by-month.pdf)
[May 2026 Building Permits with Valuations](https://www.laramiecountywy.gov/files/assets/public/v/1/may-building-permits-with-valuation-by-month.pdf)
[June 2026 Building Permits with Valuations](https://www.laramiecountywy.gov/files/assets/public/v/1/june-building-permits-with-valuation-by-month.pdf)
[July 2026 Building Permits with Valuations](https://www.laramiecountywy.gov/files/assets/public/v/1/july-building-permits-with-valuation-by-month.pdf)
[July 2025 Building Permits with Valuations](https://www.laramiecountywy.gov/files/assets/public/v/1/july-2025-building-permits.pdf)
[2026 Planning Commission Agenda](https://www.laramiecountywy.gov/files/agenda.pdf)
"""
        links = current_year_report_links(markdown, year=2026, base_url=BASE)
        self.assertEqual(len(links), 4)
        self.assertTrue(any("may-building" in link for link in links))
        self.assertTrue(any("june-building" in link for link in links))
        self.assertTrue(any("july-building" in link for link in links))
        self.assertFalse(any("2025" in link for link in links))

    def test_relative_official_pdf_links_are_resolved(self):
        markdown = """
[May 2026 Building Permits with Valuations(PDF, 128KB)](/files/assets/public/v/1/may-building-permits-with-valuation-by-month.pdf)
[June 2026 Building Permits with Valuations(PDF, 128KB)](</files/sharedassets/public/v/1/planning/documents/june-building-permits-with-valuation-by-month.pdf>)
[July 2026 Building Permits with Valuations(PDF, 131KB)](/files/assets/public/v/1/july-building-permits-with-valuation-by-month.pdf "July report")
"""
        links = current_year_report_links(markdown, year=2026, base_url=BASE)
        self.assertEqual(len(links), 3)
        self.assertTrue(all(link.startswith("https://www.laramiecountywy.gov/files/") for link in links))
        self.assertTrue(any("may-building" in link for link in links))
        self.assertTrue(any("june-building" in link for link in links))
        self.assertTrue(any("july-building" in link for link in links))

    def test_foreign_pdf_link_is_rejected(self):
        markdown = "[July 2026 Building Permits with Valuations](https://example.com/july-building-permits-with-valuations.pdf)"
        self.assertEqual(current_year_report_links(markdown, year=2026, base_url=BASE), [])


if __name__ == "__main__":
    unittest.main()
