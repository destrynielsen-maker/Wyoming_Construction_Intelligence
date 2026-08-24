import unittest
from wyoming_permits.collectors import COLLECTORS

class SourceIdentityRegressionTests(unittest.TestCase):
    def test_invalid_gillette_source_is_not_registered(self):
        self.assertNotIn("Gillette", [collector.name for collector in COLLECTORS])

if __name__ == "__main__":
    unittest.main()
