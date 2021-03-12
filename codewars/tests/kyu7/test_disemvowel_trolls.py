from unittest import TestCase

from codewars.kata.kyu7.disemvowel_trolls import disemvowel


class Test(TestCase):

    def test_disemvowel_trolls(self):
        self.assertEqual(disemvowel("Yo, This website is for losers LOL!"), "Y, Ths wbst s fr lsrs LL!")
