import unittest

from build_profile import _entry_version


class EntryVersionTests(unittest.TestCase):
    def test_uses_version_from_entry_id(self):
        entry = {
            'id': 'oai:arXiv.org:2611.00793v2',
            'summary': 'Related work: arXiv:2203.01250v3',
        }

        self.assertEqual(_entry_version(entry), '2')

    def test_ignores_versions_for_other_papers_in_summary(self):
        entry = {
            'id': 'oai:arXiv.org:2611.00793',
            'summary': 'Related work: arXiv:2203.01250v3',
        }

        self.assertIsNone(_entry_version(entry))

    def test_uses_matching_version_from_summary(self):
        entry = {
            'id': 'oai:arXiv.org:2611.00793',
            'summary': 'This is arXiv:2611.00793v4.',
        }

        self.assertEqual(_entry_version(entry), '4')

    def test_uses_link_identifier_when_entry_id_has_none(self):
        entry = {
            'id': 'announcement',
            'link': 'https://arxiv.org/abs/2611.00793',
            'summary': 'This is arXiv:2611.00793v4.',
        }

        self.assertEqual(_entry_version(entry), '4')


if __name__ == '__main__':
    unittest.main()
