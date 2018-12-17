import unittest
from .word_count import get_most_common_words
from .word_count import get_wikipedia_page, parse_wikipedia_page
from .word_count import gather_parsed_wikipedia_pages_by_title, get_wikipedia_pages_by_title
from .word_count import WAIT_FOR_CONNECTION_CLOSE
import aiohttp
import asyncio


class TestGetMostCommonWords(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Call the word count on a list of titles for all tests once - call is expensive"""
        titles = ['Monty Python and the Holy Grail', 'there is no such page with this title', 'Monty Python',
                  'Terry Gilliam', '', 'Application_programming_interface', 'Robotic process automation',
                  'IBM_Spectrum_Scale', 'William Hartnell']
        cls.ranking = get_most_common_words(titles)

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

    async def run_get_wikipedia_page(self, title: str) -> dict:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            return await get_wikipedia_page(session, title)

    async def run_parse_wikipedia_page(self, title: str) -> str:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            return await parse_wikipedia_page(session, title)

    def setUp(self):
        # see also: https://stackoverflow.com/a/23642269/4703154
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()

    def test_get_wikipedia_page_returns_contents_as_json(self):
        """Test that the contents of a page are fetched and returned as wm json"""
        title = 'Monty Python and the Holy Grail'
        wmpage = self.loop.run_until_complete(self.run_get_wikipedia_page(title))
        self.assertIsInstance(wmpage, dict)
        # the json dict should contain the following fields, field 'warnings' is optional
        for field in ['continue', 'query']:
            self.assertIn(field, wmpage)
        # query field has one key: pages, which itself is a dict with one key, a page id
        # that page id dict contains the pageid, ns, title and revisions
        for pageid, page in wmpage.get('query', {}).get('pages', {}).items():
            self.assertIsInstance(page, dict)
            self.assertEqual(title, page.get('title', ''))
            self.assertIn('revisions', page)

    def test_get_wikipedia_page_accepts_empty_title(self):
        wmpage = self.loop.run_until_complete(self.run_get_wikipedia_page(''))
        self.assertIsInstance(wmpage, dict)
        self.assertIn('batchcomplete', wmpage)
        self.assertFalse(wmpage.get('query', {}).get('pages', {}).get('revisions'))

    def test_parse_contents_returns_empty_string_on_title_does_not_exist(self):
        c = self.loop.run_until_complete(self.run_parse_wikipedia_page('there is no such page with this title'))
        self.assertIsInstance(c, str)
        self.assertFalse(c)

    def test_parse_contents_returns_empty_string_on_empty_title(self):
        c = self.loop.run_until_complete(self.run_parse_wikipedia_page(''))
        self.assertIsInstance(c, str)
        self.assertFalse(c)

    def test_parse_contents_returns_non_empty_string_on_existing_title(self):
        c = self.loop.run_until_complete(self.run_parse_wikipedia_page('Monty Python and the Holy Grail'))
        self.assertIsInstance(c, str)
        self.assertTrue(c)  # non-empty string

    def tearDown(self):
        self.loop.run_until_complete(asyncio.sleep(WAIT_FOR_CONNECTION_CLOSE))
        self.loop.close()


class TestGatherPages(unittest.TestCase):

    async def run_gather_parsed_wikipedia_pages_by_title(self, titles):
        return await gather_parsed_wikipedia_pages_by_title(titles)

    @classmethod
    def setUpClass(cls):
        cls.titles = ['Monty Python and the Holy Grail', 'there is no such page with this title', 'Monty Python',
                      'Terry Gilliam', '', 'Application_programming_interface', 'Robotic process automation',
                      'IBM_Spectrum_Scale', 'William Hartnell']

    def setUp(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.parsed_pages = self.loop.run_until_complete(self.run_gather_parsed_wikipedia_pages_by_title(self.titles))

    def test_gather_pages_returns_list(self):
        self.assertIsInstance(self.parsed_pages, list)

    def test_gather_pages_returns_list_of_same_length_as_titles(self):
        self.assertEqual(len(self.titles), len(self.parsed_pages))

    def test_gather_pages_returns_list_of_strings(self):
        self.assertEqual(len(self.parsed_pages),
                         len([p for p in self.parsed_pages if isinstance(p, str)]))

    def tearDown(self):
        self.loop.run_until_complete(asyncio.sleep(WAIT_FOR_CONNECTION_CLOSE))
        self.loop.close()


class TestGetPagesByTitle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.titles = ['Monty Python and the Holy Grail', 'there is no such page with this title', 'Monty Python',
                      'Terry Gilliam', '', 'Application_programming_interface', 'Robotic process automation',
                      'IBM_Spectrum_Scale', 'William Hartnell']
        cls.parsed_pages = get_wikipedia_pages_by_title(cls.titles)

    def test_get_pages_returns_list(self):
        self.assertIsInstance(self.parsed_pages, list)

    def test_get_pages_returns_list_of_same_length_as_titles(self):
        self.assertEqual(len(self.titles), len(self.parsed_pages))

    def test_get_pages_returns_list_of_strings(self):
        self.assertEqual(len(self.parsed_pages),
                         len([p for p in self.parsed_pages if isinstance(p, str)]))
