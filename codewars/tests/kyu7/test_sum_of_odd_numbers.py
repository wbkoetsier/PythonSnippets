from unittest import TestCase

from codewars.kata.kyu7.sum_of_odd_numbers import row_sum_odd_numbers


class Test(TestCase):
    def test_row_sum_odd_numbers1(self):
        self.assertEqual(row_sum_odd_numbers(1), 1)

    def test_row_sum_odd_numbers2(self):
        self.assertEqual(row_sum_odd_numbers(2), 8)

    def test_row_sum_odd_numbers3(self):
        self.assertEqual(row_sum_odd_numbers(13), 2197)

    def test_row_sum_odd_numbers4(self):
        self.assertEqual(row_sum_odd_numbers(19), 6859)

    def test_row_sum_odd_numbers5(self):
        self.assertEqual(row_sum_odd_numbers(41), 68921)
