import unittest
from .word_count import word_ranking, get_wikipedia_page, parse_wiki_page


@unittest.skip
class TestWordCount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Call the word count on a list of titles for all tests once - call is expensive"""
        titles = ['Monty Python and the Holy Grail', 'there is no such page with this title', 'Monty Python',
                  'Terry Gilliam', 'Application_programming_interface', 'Robotic process automation',
                  'IBM_Spectrum_Scale', 'William Hartnell']
        cls.ranking = word_ranking(titles)

    def test_returns_word_ranking_as_list_of_tuples(self):
        self.assertIsInstance(self.ranking, list)
        for elem in self.ranking:
            self.assertIsInstance(elem, tuple)
            self.assertIsInstance(elem[0], str)
            self.assertIsInstance(elem[1], int)

    def test_ranking_is_reverse_ordered(self):
        counts = [c[1] for c in self.ranking]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_no_duplicate_words_in_ranking(self):
        words = [w[0] for w in self.ranking]
        self.assertEqual(len(words), len(set(words)))


class TestGetSingleWikipediaPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.title = 'Monty Python and the Holy Grail'
        cls.wmpage = get_wikipedia_page(cls.title)

    def test_get_wikipedia_page_returns_contents_as_json(self):
        """Test that the contents of a page are fetched and returned as wm json"""
        self.assertIsInstance(self.wmpage, dict)
        # the json dict should contain the following fields, field 'warnings' is optional
        for field in ['continue', 'query']:
            self.assertIn(field, self.wmpage)
        # query field has one key: pages, which itself is a dict with one key, a page id
        # that page id dict contains the pageid, ns, title and revisions
        for pageid, page in self.wmpage.get('query', {}).get('pages', {}).items():
            self.assertIsInstance(page, dict)
            self.assertEqual(self.title, page.get('title', ''))
            self.assertIn('revisions', page)

    # @unittest.skip('expensive')
    def test_get_wikipedia_page_accepts_empty_title(self):
        r = get_wikipedia_page('')
        self.assertIsInstance(r, dict)
        self.assertIn('batchcomplete', r)
        self.assertFalse(r.get('query', {}).get('pages', {}).get('revisions'))

    def test_parse_contents_returns_empty_string_on_title_does_not_exist(self):
        title = 'there is no such page with this title'
        r = get_wikipedia_page(title)
        self.assertIsInstance(r, dict)
        self.assertIn('batchcomplete', r)
        c = parse_wiki_page(r, title)
        self.assertIsInstance(c, str)
        self.assertFalse(c)

    def test_parse_contents_returns_empty_string_on_empty_title(self):
        r = get_wikipedia_page('')
        c = parse_wiki_page(r, '')
        self.assertIsInstance(c, str)
        self.assertFalse(c)

    def test_parse_contents_returns_non_empty_string_on_existing_title(self):
        c = parse_wiki_page(self.wmpage, self.title)
        self.assertIsInstance(c, str)
        self.assertTrue(c)  # non-empty string
