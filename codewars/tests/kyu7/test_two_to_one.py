from unittest import TestCase

from codewars.kata.kyu7.two_to_one import longest


class Test(TestCase):

    def test_longest1(self):
        self.assertEqual(longest("aretheyhere", "yestheyarehere"), "aehrsty")

    def test_longest2(self):
        self.assertEqual(longest("loopingisfunbutdangerous", "lessdangerousthancoding"), "abcdefghilnoprstu")

    def test_longest3(self):
        self.assertEqual(longest("inmanylanguages", "theresapairoffunctions"), "acefghilmnoprstuy")
