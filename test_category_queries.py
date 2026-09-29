import unittest
from category_queries import category_queries

class CategoryQueryTests(unittest.TestCase):
    def test_arbitrary_custom_categories_and_dedup(self):
        self.assertEqual(category_queries(["Cafes"], "custom niche, cafes, Cafeterias"),
                         ["Cafes", "custom niche", "Cafeterias"])

if __name__ == "__main__":
    unittest.main()
