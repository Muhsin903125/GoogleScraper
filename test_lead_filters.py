import unittest
from lead_filters import filter_rows, facet_values


class LocalFilterTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"Company Name": "Acme Cafe", "Website": "None", "Intl Phone": "+971 50 123 4567", "Email": "hi@acme.test", "Category": "Cafe", "Emirate": "Dubai", "Area": "Marina", "Rating": "4.7", "Reviews": "1,200"},
            {"Company Name": "Beta Clinic", "Website": "https://beta.test", "Phone": "04 333 3333", "Category": "Clinic", "Emirate": "Sharjah", "Area": "Majaz", "Rating": "3.1", "Reviews": "12"},
            {"Company Name": "Gamma Cafe", "Website": "", "Category": "Cafe", "Emirate": "Dubai", "Area": "Deira", "Rating": "", "Reviews": ""},
        ]

    def test_presence_is_distinct_from_mobile_format(self):
        self.assertEqual([r["Company Name"] for r in filter_rows(self.rows, website="Has")], ["Beta Clinic"])
        self.assertEqual([r["Company Name"] for r in filter_rows(self.rows, email="Has", mobile="Has")], ["Acme Cafe"])
        self.assertEqual([r["Company Name"] for r in filter_rows(self.rows, phone="Missing")], ["Gamma Cafe"])

    def test_facets_and_name_are_combined(self):
        self.assertEqual([r["Company Name"] for r in filter_rows(self.rows, categories=["Cafe"], emirates=["Dubai"], areas=["Marina"], name_keyword="ACME")], ["Acme Cafe"])
        self.assertEqual(facet_values(self.rows, "Category"), ["Cafe", "Clinic"])

    def test_numeric_bounds_and_missing_values(self):
        self.assertEqual([r["Company Name"] for r in filter_rows(self.rows, min_rating=4, max_rating=5, min_reviews=100, max_reviews=2000)], ["Acme Cafe"])
        self.assertEqual(filter_rows(self.rows, max_rating=2), [])

    def test_whatsapp_possible_label_does_not_verify_account(self):
        rows = [{"Mobile": "", "WhatsApp Possible": "Yes"}, {"WhatsApp Possible": "No"}]
        self.assertEqual(filter_rows(rows, mobile="Has"), rows[:1])
        self.assertEqual(filter_rows(rows, mobile="Missing"), rows[1:])


if __name__ == "__main__":
    unittest.main()
