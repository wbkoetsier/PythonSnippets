from typing import Union, List, Tuple
import requests
import mwparserfromhell


API_URL = "https://en.wikipedia.org/w/api.php"


def word_ranking(titles: List=[]) -> List[Tuple[str, int]]:
    return [('word', 10), ('the', 1)]


def get_wikipedia_page(title: str="") -> dict:
    params = {"action": "query", "prop": "revisions", "rvlimit": 1,
              "rvprop": "content", "format": "json", "titles": title}
    r = requests.get(API_URL, params=params)
    if not r.status_code == 200:
        raise ValueError(f"Unable to fetch page '{title}', WikiMedia responded with a {r.status_code}")
    return r.json()


def parse_wiki_page(wmpage: dict, title: str) -> str:
    """Extract the text contents of the given wikipedia page"""
    pages = wmpage.get('query', {}).get('pages', {})
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
