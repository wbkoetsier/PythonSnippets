import requests
import mwparserfromhell
from collections import Counter
from typing import List, Union
import time

__all__ = ['get_most_common_words']


API_URL = "https://en.wikipedia.org/w/api.php"
TRANSLATION_TABLE = str.maketrans('', '', '()/\\.,;:\'\"*&-')


def parse_wiki_page(title: str) -> Union[str, None]:
    """Return the text contents of this Wikipedia page"""
    params = {"action": "query", "prop": "revisions", "rvlimit": 1,
              "rvprop": "content", "format": "json", "titles": title}
    r = requests.get(API_URL, params=params)
    if not r.status_code == 200:
        raise ValueError(f"Unable to fetch page '{title}', WikiMedia responded with a {r.status_code}")
    result = r.json()
    pages = result.get('query', {}).get('pages', {})
    # rvlimit is 1, so there'll be 1 page/revision
    (page_id, page) = pages.popitem() if pages else (-1, None)
    if str(page_id) == '-1':
        print(f"No page found with title '{title}'")
        return ''
    rev = page.get('revisions', [])
    # each revision has a key '*' that contains the actual contents
    if rev:
        page_content = rev[0].get('*', '')
    else:
        return ''
    parsed_content = mwparserfromhell.parse(page_content)
    return parsed_content.strip_code(collapse=False)


def count_words(text: str) -> Counter:
    """Return a dictionary of word: #occurences as found in the text."""
    trans = text.translate(TRANSLATION_TABLE)
    cntr = Counter()
    for word in trans.split():
        cntr[word.lower()] += 1
    return cntr


def get_most_common_words(titles: List[str], top: int=10) -> list:
    """Return a list of the most common words as found in the Wikipedia pages with the given titles"""
    start = time.time()
    text = ''
    for title in titles:
        wiki = parse_wiki_page(title)
        if not wiki:
            continue
        text += wiki
    print('gathering all pages took {:.2f} seconds'.format(time.time() - start))
    cntr = count_words(text)
    return cntr.most_common(top)


if __name__ == '__main__':
    titles = ['Monty Python and the Holy Grail', 'there is no such page with this title', 'Monty Python',
              'Terry Gilliam', '', 'Application_programming_interface', 'Robotic process automation',
              'IBM_Spectrum_Scale', 'William Hartnell']
    wrds = get_most_common_words(titles)
    print(wrds)
