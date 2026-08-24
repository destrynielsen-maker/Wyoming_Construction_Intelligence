import tempfile, unittest, xml.etree.ElementTree as ET
from pathlib import Path
from wyoming_permits.models import Permit
from wyoming_permits.feeds import write_all_feeds

class FeedTests(unittest.TestCase):
    def test_xml(self):
        p=Permit(state="WY",jurisdiction="Gillette",permit_number="1",issued_date="2026-08-20",project_name="New warehouse",classification="COMMERCIAL",qualifies=True,score=50)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d); write_all_feeds(out,[p],"https://example.test/")
            for name in ["new-construction.xml","single-family.xml","multifamily.xml","commercial.xml","top-opportunities.xml"]: ET.parse(out/name)

if __name__=="__main__": unittest.main()
