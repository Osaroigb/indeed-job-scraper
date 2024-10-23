import unittest
from jobs.link_generator import generate_url

class TestLinkGenerator(unittest.TestCase):
    
    def test_generate_url(self):
        self.assertEqual(generate_url("paediatric nurse"), "https://uk.indeed.com/jobs?q=paediatric+nurse&l=London")
        self.assertEqual(generate_url("software engineer"), "https://uk.indeed.com/jobs?q=software+engineer&l=London")
        self.assertEqual(generate_url("data scientist"), "https://uk.indeed.com/jobs?q=data+scientist&l=London")

if __name__ == "__main__":
    unittest.main()