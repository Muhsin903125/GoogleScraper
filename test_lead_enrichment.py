import csv
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import lead_enrichment as lead


class EnrichmentTests(unittest.TestCase):
    def test_mobile_is_format_only(self):
        self.assertEqual(lead.mobile_number('050 123 4567'), '+971501234567')
        self.assertEqual(lead.mobile_number('+971 58 123 4567'), '+971581234567')
        self.assertEqual(lead.mobile_number('+971 4 123 4567'), '')

    def test_extract_public_email_social_and_provenance(self):
        html = '<div>Contact hello@example.com</div><a href="mailto:sales@example.com">Email</a><a href="tel:+971501234567">Call</a><a href="https://instagram.com/test">Social</a>'
        result = lead.extract(html, 'https://example.com/contact')
        self.assertEqual(result['Email'], 'hello@example.com; sales@example.com')
        self.assertEqual(result['Mobile'], '+971501234567')
        self.assertEqual(result['Contact Source URL'], 'https://example.com/contact')
        self.assertIn('instagram.com', result['Social URLs'])

    def test_reject_private_urls(self):
        for url in ('http://127.0.0.1/', 'http://localhost/', 'file:///etc/passwd', 'http://169.254.169.254/latest/meta-data/'):
            self.assertIsNone(lead.public_url(url))

    def test_keyless_csv_filters_with_mocked_public_site(self):
        with tempfile.TemporaryDirectory() as directory:
            inp, out = os.path.join(directory, 'in.csv'), os.path.join(directory, 'out.csv')
            with open(inp, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'Mobile'])
                writer.writeheader()
                writer.writerow({'Company Name': 'Acme', 'Website': 'https://example.com/', 'Mobile': '0501234567'})
                writer.writerow({'Company Name': 'NoEmail', 'Website': '', 'Mobile': '04 123 4567'})
            with patch.object(lead, 'public_url', side_effect=lambda url: url if url else None), patch.object(lead, 'fetch_page', return_value=('<a href="mailto:hello@example.com">Hi</a>', 'https://example.com/')):
                with patch('sys.argv', ['lead_enrichment.py', inp, out, '--has-email', '--has-mobile']):
                    lead.main()
            with open(out, newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['Email'], 'hello@example.com')
            self.assertEqual(rows[0]['WhatsApp Possible'], 'yes')

    def test_typesafe_ambiguous_candidates_not_selected(self):
        fake = Mock()
        fake.post.return_value.json.return_value = {'answers': {'candidate_0': {'type':'noul','noul':.97}, 'candidate_1': {'type':'noul','noul':.97}}}
        fake.post.return_value.raise_for_status.return_value = None
        candidates = [{'url':'https://a.example'}, {'url':'https://b.example'}]
        self.assertEqual(lead.typesafe_match('Acme', 'Dubai', candidates, 'key', fake), '')
        questions = fake.post.call_args.kwargs['json']['questions']
        self.assertIn('candidates[1]', questions['candidate_1']['instructions'])


if __name__ == '__main__':
    unittest.main()
