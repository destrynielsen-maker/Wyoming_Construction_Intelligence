import unittest
from wyoming_permits.models import Permit
from wyoming_permits.classify import classify_permit

class ClassifyTests(unittest.TestCase):
    def test_multifamily(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="1",issued_date="2026-08-20",permit_type="Commercial Building",project_name="New 24-unit apartment building",valuation=5_000_000,owner="Example")
        classify_permit(p); self.assertTrue(p.qualifies); self.assertEqual(p.classification,"MULTIFAMILY"); self.assertEqual(p.units,24); self.assertGreaterEqual(p.score,60)
    def test_single_family(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="2",issued_date="2026-08-20",permit_type="New Single Family Residence",project_name="New dwelling"); classify_permit(p); self.assertEqual(p.classification,"SINGLE_FAMILY"); self.assertTrue(p.qualifies)
    def test_commercial(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="3",issued_date="2026-08-20",permit_type="Commercial Building",project_name="New warehouse building",valuation=2_000_000); classify_permit(p); self.assertEqual(p.classification,"COMMERCIAL"); self.assertTrue(p.qualifies)
    def test_remodel_excluded(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="4",issued_date="2026-08-20",permit_type="Commercial Building",project_name="Office remodel"); classify_permit(p); self.assertFalse(p.qualifies)

if __name__=="__main__": unittest.main()
