from unittest import TestCase

from codewars.kata.kyu6.format_name_string import namelist


class Test(TestCase):
    def test_namelist_5names(self):
        self.assertEqual('Bart, Lisa, Maggie, Homer & Marge',
                         namelist([{'name': 'Bart'}, {'name': 'Lisa'}, {'name': 'Maggie'},
                                   {'name': 'Homer'}, {'name': 'Marge'}]),
                         "Must work with many names")

    def test_namelist_3names(self):
        self.assertEqual('Bart, Lisa & Maggie',
                         namelist([{'name': 'Bart'}, {'name': 'Lisa'}, {'name': 'Maggie'}]),
                         "Must work with many names")

    def test_namelist_2names(self):
        self.assertEqual('Bart & Lisa',
                         namelist([{'name': 'Bart'}, {'name': 'Lisa'}]),
                         "Must work with two names")

    def test_namelist_1name(self):
        self.assertEqual('Bart',
                         namelist([{'name': 'Bart'}]),
                         "Wrong output for a single name")

    def test_namelist_0names(self):
        self.assertEqual('',
                         namelist([]),
                         "Must work with no names")
