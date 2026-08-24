import unittest
from datetime import datetime, timezone
from wyoming_permits.collectors.gillette import GilletteCollector

class GilletteTests(unittest.TestCase):
    def test_attributes(self):
        ms=int(datetime(2026,8,20,tzinfo=timezone.utc).timestamp()*1000)
        p=GilletteCollector()._from_attributes({"Permit":"BP-26-00123","Type":"Commercial Building","Prefix":"BLD","Status_1":"Issued","Address":"123 MAIN ST","District":"CITY","VALUE":2500000,"SqFt":30000,"DESCRIPTION":"New warehouse building","ISSUEDATE":ms,"APPLYDATE":ms,"Owner":"Example Owner LLC","CSS_url":"https://example.test/permit"})
        self.assertIsNotNone(p); self.assertEqual(p.permit_number,"BP-26-00123"); self.assertEqual(p.issued_date,"2026-08-20"); self.assertEqual(p.valuation,2500000.0); self.assertEqual(p.owner,"Example Owner LLC"); self.assertEqual(p.source_url,"https://example.test/permit")

if __name__=="__main__": unittest.main()
