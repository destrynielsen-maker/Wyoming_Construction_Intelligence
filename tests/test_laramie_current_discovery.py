import unittest

from wyoming_permits.collectors.laramie_county_current import current_year_report_links


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
        links = current_year_report_links(markdown, year=2026)
        self.assertEqual(len(links), 4)
        self.assertTrue(any("may-building" in link for link in links))
        self.assertTrue(any("june-building" in link for link in links))
        self.assertTrue(any("july-building" in link for link in links))
        self.assertFalse(any("2025" in link for link in links))


if __name__ == "__main__":
    unittest.main()
