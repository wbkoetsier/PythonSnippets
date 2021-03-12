# https://www.codewars.com/kata/52fba66badcd10859f00097e
import re


def disemvowel(input):
    return re.sub('[aeiou]', '', input, flags=re.IGNORECASE | re.MULTILINE)
