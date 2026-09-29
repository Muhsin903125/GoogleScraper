import unittest
from lead_search import search_rows


class LeadSearchTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {'Company Name':'Alpha Cafe','City':'Dubai','Business Category':'Coffee Shops','Email':'a@example.com'},
            {'Company Name':'Beta Gym','City':'Abu Dhabi','Business Category':'Fitness'},
            {'Company Name':'Gamma Cafe','City':'Sharjah','Business Category':'Coffee Shops'},
        ]

    def test_terms_across_location_and_category(self):
        self.assertEqual(search_rows(self.rows, 'DuBaI coffee'), self.rows[:1])
        self.assertEqual(search_rows(self.rows, 'fitness abu dhabi'), self.rows[1:2])

    def test_quoted_phrase(self):
        self.assertEqual(search_rows(self.rows, '"coffee shops" Sharjah'), self.rows[2:])

    def test_empty_returns_all(self):
        self.assertEqual(search_rows(self.rows, ''), self.rows)

    def test_non_search_fields_do_not_match(self):
        self.assertEqual(search_rows(self.rows, 'example.com'), [])


if __name__ == '__main__':
    unittest.main()
