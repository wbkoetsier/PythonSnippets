from unittest import TestCase

from codewars.kata.kyu6.equal_sides_of_an_array import find_even_index


class Test(TestCase):
    def test_find_even_index1(self):
        self.assertEqual(find_even_index([1, 2, 3, 4, 3, 2, 1]), 3)

    def test_find_even_index2(self):
        self.assertEqual(find_even_index([1, 100, 50, -51, 1, 1]), 1, )

    def test_find_even_index3(self):
        self.assertEqual(find_even_index([1, 2, 3, 4, 5, 6]), -1)

    def test_find_even_index4(self):
        self.assertEqual(find_even_index([20, 10, 30, 10, 10, 15, 35]), 3)

    def test_find_even_index5(self):
        self.assertEqual(find_even_index([20, 10, -80, 10, 10, 15, 35]), 0)

    def test_find_even_index6(self):
        self.assertEqual(find_even_index([10, -80, 10, 10, 15, 35, 20]), 6)

    def test_find_even_index7(self):
        self.assertEqual(find_even_index(list(range(1, 100))), -1)

    def test_find_even_index8(self):
        self.assertEqual(find_even_index([0, 0, 0, 0, 0]), 0, "Should pick the first index if more cases are valid")

    def test_find_even_index9(self):
        self.assertEqual(find_even_index([-1, -2, -3, -4, -3, -2, -1]), 3)

    def test_find_even_index10(self):
        self.assertEqual(find_even_index(list(range(-100, -1))), -1)
