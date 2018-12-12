import unittest
from .word_count import word_ranking


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
