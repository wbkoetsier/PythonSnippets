import requests
from word_count_async.word_count import get_most_common_words as async_word_count, API_URL
from word_count_v1 import get_most_common_words as word_count_v1
from typing import List, Tuple
import time


def get_random_titles(number_of_titles: int=10) -> List[str]:
    params = {'action': 'query', 'list': 'random', 'format': 'json', 'rnnamespace': '0',
              'rnlimit': number_of_titles}
    r = requests.get(url=API_URL, params=params)
    assert r.status_code == 200
    result = r.json()
    return [t.get('title', 'unable to find title') for t in result.get('query', {}).get('random', [])]


def add_special_titles(titles: List[str]) -> List[str]:
    """Return a new list of titles with some special cases added to the input list"""
    special_cases = ['', 'there is no page with this title']
    titles += special_cases
    return titles


def benchmark_word_count(titles: List[str], top: int=10, iterations: int=10) -> Tuple[list, list]:
    results_v1 = []
    results_async = []
    for _ in range(iterations):
        print('start word count v1')
        start_v1 = time.time()
        wrds_v1 = word_count_v1(titles, top)
        end_v1 = time.time() - start_v1
        print('results of word count v1:', wrds_v1)
        print('\nword count v1 took {:.2f} seconds\n'.format(end_v1))
        results_v1.append('{:.2f}'.format(end_v1))

        print('start async word count')
        start_v2 = time.time()
        wrds_async = async_word_count(titles, top)
        end_v2 = time.time() - start_v2
        print('results of async word count:', wrds_async)
        print('\nasync word count took {:.2f} seconds'.format(end_v2))
        results_async.append('{:.2f}'.format(end_v2))

        print('==========')
    return results_v1, results_async


if __name__ == '__main__':

    number_of_titles = 100
    top = 10
    iterations = 1

    titles = add_special_titles(get_random_titles(100))

    times_v1, times_async = benchmark_word_count(titles, top, iterations)

    print('\n===============\nRESULTS')
    print(f'top: {top}, iterations: {iterations}, titles: {titles}')
    print('For v1:   ', times_v1)
    print('For async:', times_async)
