from unittest import TestCase

from codewars.kata.kyu6.arraydiff import array_diff


class TestArrayDiff(TestCase):

    def test_array_diff1(self):
        self.assertEqual(array_diff([1, 2], [1]), [2], "a was [1,2], b was [1], expected [2]")

    def test_array_diff2(self):
        self.assertEqual(array_diff([1, 2, 2], [1]), [2, 2], "a was [1,2,2], b was [1], expected [2,2]")

    def test_array_diff3(self):
        self.assertEqual(array_diff([1, 2, 2], [2]), [1], "a was [1,2,2], b was [2], expected [1]")

    def test_array_diff4(self):
        self.assertEqual(array_diff([1, 2, 2], []), [1, 2, 2], "a was [1,2,2], b was [], expected [1,2,2]")

    def test_array_diff5(self):
        self.assertEqual(array_diff([], [1, 2]), [], "a was [], b was [1,2], expected []")
