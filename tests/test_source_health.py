import unittest
from datetime import date
from types import SimpleNamespace
from wyoming_permits.models import Permit
from wyoming_permits.pipeline import _success, _fail

class HealthTests(unittest.TestCase):
    def test_fresh_success(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="1",issued_date="2026-08-20"); result=SimpleNamespace(source="Gillette",permits=[p],source_url="x",note="ok"); status=_success(result,1,None,"2026-08-24T00:00:00+00:00",date(2026,8,24),14); self.assertEqual(status["status"],"healthy"); self.assertEqual(status["days_since_newest_permit"],4)
    def test_stale_success(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="1",issued_date="2026-07-01"); result=SimpleNamespace(source="Gillette",permits=[p],source_url="x",note="ok"); status=_success(result,1,None,"2026-08-24T00:00:00+00:00",date(2026,8,24),14); self.assertEqual(status["status"],"stale")

if __name__=="__main__": unittest.main()
