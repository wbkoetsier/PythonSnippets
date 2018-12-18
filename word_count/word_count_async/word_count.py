from typing import List
import mwparserfromhell
import aiohttp
import asyncio
import time
from collections import Counter
from string import punctuation

__all__ = ['get_most_common_words', 'API_URL']

TRANSLATION_TABLE = str.maketrans('', '', punctuation)
API_URL = "https://en.wikipedia.org/w/api.php"
CONCURRENCY = 10  # asyncio.Semaphore defaults to 1
# When closing event loop, wait x seconds for the underlying SSL connections to close
# see https://aiohttp.readthedocs.io/en/stable/client_advanced.html#graceful-shutdown
WAIT_FOR_CONNECTION_CLOSE = 0.250


async def get_wikipedia_page(session: aiohttp.ClientSession, title: str) -> dict:
    """This coroutine returns the response data for the given Wikipedia page title (json)"""
    params = {"action": "query", "prop": "revisions", "rvlimit": 1,
              "rvprop": "content", "format": "json", "titles": title}
    async with asyncio.Semaphore(CONCURRENCY), session.get(url=API_URL, params=params) as response:
        assert response.status == 200
        data = await response.json()
    return data


async def parse_wikipedia_page(session: aiohttp.ClientSession, title: str) -> str:
    """Extract the text contents of the given wikipedia page"""
    wmpage = await get_wikipedia_page(session, title)
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


async def gather_parsed_wikipedia_pages_by_title(titles: List[str]) -> List[dict]:
    """This coroutine fetches results for every title in the list and returns the results as a list.

    Sort order is preserved (see also the docs on asyncio.gather and https://github.com/python/asyncio/issues/432).
    """
    # print('start get')
    # start = time.time()
    # the session shouldn't be created outside of a coroutine so it needs to be here rather than in a constructor
    # see also https://github.com/aio-libs/aiohttp/issues/2473
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        # create coroutines for fetching each url
        coroutines = (parse_wikipedia_page(session=session, title=title) for title in titles)
        # gather the responses, add any exceptions to the list instead of raising
        responses = await asyncio.gather(*coroutines, return_exceptions=True)
    # print('gathering all pages took {:.2f} seconds'.format(time.time() - start))
    return responses


def get_wikipedia_pages_by_title(titles: List[str]) -> List[str]:
    """Set up event loop, run gatherer with the list of titles, close event loop"""
    # make sure the event loop is always a new one, because we can't reopen an already closed loop and also we don't
    # want to restart the interpreter between calls to parallel.my_method
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(gather_parsed_wikipedia_pages_by_title(titles))
    loop.run_until_complete(asyncio.sleep(WAIT_FOR_CONNECTION_CLOSE))
    loop.close()
    return result


def count_words(text: str) -> Counter:
    """Return a dictionary of word: #occurences as found in the text."""
    trans = text.translate(TRANSLATION_TABLE)
    cntr = Counter()
    for word in trans.split():
        cntr[word.lower()] += 1
    return cntr


def get_most_common_words(titles: List[str], top: int=10) -> list:
    """Return a list of the most common words as found in the Wikipedia pages with the given titles"""
    text = '\n'.join(get_wikipedia_pages_by_title(titles))
    cntr = count_words(text)
    return cntr.most_common(top)


if __name__ == '__main__':
    titles = ['Monty Python and the Holy Grail', 'there is no such page with this title', 'Monty Python',
              'Terry Gilliam', '', 'Application_programming_interface', 'Robotic process automation',
              'IBM_Spectrum_Scale', 'William Hartnell']
    ranking = get_most_common_words(titles, 10)
    print('ranking:', ranking)
