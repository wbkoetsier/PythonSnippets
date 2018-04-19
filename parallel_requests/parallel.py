import aiohttp
import asyncio
from functools import partial
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from typing import Union


__all__ = ['get']

TIMEOUT = 300  # 300 is the default
CONCURRENCY = 1000  # Semaphore defaults to 1
OFFSET = 0
BATCH_LIMIT = 1000


class RequestCaller:
    """Call the appropriate request on all urls found in the list items in parallel
    and aggregate and return the responses"""

    def __init__(self, headers: dict=None):
        # use a semaphore to make sure no more than CONCURRENCY requests run at the same time
        self.semaphore = asyncio.Semaphore(CONCURRENCY)

    async def fetch(self, session: aiohttp.ClientSession,
                    url: str, params: dict=None, headers: dict=None) -> Union[dict, list]:
        """This coroutine returns the response data for the given url (json)
        If the url responds with a list, the separate items are fetched and returned as a list.
        If limit is set to -1, all items will be fetched in batches, recursively until no more items are found.
        """
        print(f'start fetch_url {url}')
        start = time.time()
        # first, catch the limit, because if -1 is given this means no limit, which we will fetch in per LIMIT batches
        fetch_all = False
        if params:
            # limit can be int, single number as a str or multiple numbers as a str comma separated
            limit = params.get('limit', '1')
            if isinstance(limit, str):
                limit = max([int(i) for i in params.get('limit', '1').split(',')])
            if limit == -1:
                fetch_all = True
                params['limit'] = BATCH_LIMIT

        # catch any exception and add an argument: the resource. This way the caller can always check
        # which exception occurred on which resource
        try:
            async with self.semaphore, session.get(url=url, params=params, headers=headers, timeout=TIMEOUT) as response:
                data = await response.json()
        except asyncio.TimeoutError as te:
            # TODO: should we retry this request? How many times?
            te.args += (f'timeout on resource: {url}',)
            print(f'timeout on fetching {url}: {te}')
            raise
        except Exception as e:
            e.args += (f'resource: {url}',)
            print(f'something went wrong fetching {url}: {e}')
            raise
        print('fetching {} took {:.2f} seconds'.format(url, time.time() - start))
        if isinstance(data, (dict, str)):
            return data
        elif isinstance(data, list):
            if data:
                # TODO: provide an option for the user to specify what the self href looks like
                # for now, assume a yourapi response
                urls = [d['_href_'] for d in data if d.get('_href_')]
                coros = (self.fetch(session=session,
                                    url=url, params=None, headers=headers)
                         for url in urls)
                responses = await asyncio.gather(*coros, return_exceptions=True)
                # if necessary, fetch next batch, until the last item is reached
                if fetch_all:
                    params['limit'] = -1
                    params['offset'] = int(params.get('offset', OFFSET)) + BATCH_LIMIT
                    r = await asyncio.ensure_future(self.fetch(session=session,
                                                               url=url, params=params, headers=headers))
                    if not r:
                        # last batch reached
                        return responses
                    else:
                        # add the items to the list
                        responses.extend(r)
                return responses
            else:
                # no more items to fetch
                return data  # []

    async def get(self, items: list, headers: dict=None) -> list:
        """This coroutine fetches results (items) for the url retrieved from every item in the list and returns the
        results as a list

        Each item in the input list can be one of:
        - a url as a string, query params can be given in the url using standard question mark/ampersand notation
        - a dictionary providing:
          - url, may include query parameters in standard question mark/ampersand notation
          - optional params: query parameters as a dict, ignored when url is used,
          - optional headers: headers as a dict, will override headers given outside the list of url items for this url

        limit=-1 will retrieve all items from offset to the very last item (in batches of BATCH_LIMIT). If multiple
        values are given, the max is used.

        As for the url, if it represents a single item this item will be returned, but if it represents a list, all
        items will be fetched and returned as a list. The final response is a list with lists and/or single items.

        Sort order is preserved (see also the docs on asyncio.gather and https://github.com/python/asyncio/issues/432).
        """
        print('start get')
        # unpack the list of items into dicts: url, params, headers
        urls = []
        for item in items:
            if isinstance(item, str):
                url = item
                params = None
                headers = None  # use session-wide headers
            elif isinstance(item, dict):
                if item.get('_href_'):
                    # hang on, this is a yourapi response body
                    url = item.get('_href_')
                    params = None  # obviously
                    headers = None  # use global session headers
                else:
                    # then this must be a dict with url
                    params = item.get('params')
                    url = item.get('url')
                    headers = item.get('headers')
            else:
                print(f'invalid item type (should be str or dict), omitting: {item}')
                break
            # unpack params from url and convert to dict to ease further processing
            parts = urlsplit(url)
            query = parse_qsl(parts.query)
            if query:
                # we have a query in the url, create new params dict
                params = {i[0]: i[1] for i in query}
                # and remove the params from the url
                new_parts = list(parts)
                new_parts[3] = ''
                url = urlunsplit(new_parts)
            urls.append(dict(url=url, params=params, headers=headers))

        start = time.time()
        # the session shouldn't be created outside of a coroutine so it needs to be here rather than in __init__
        # see also https://github.com/aio-libs/aiohttp/issues/2473
        async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
            # create coroutines for fetching each url
            coroutines = (self.fetch(session=session,
                                         url=url.get('url'), params=url.get('params'), headers=url.get('headers'))
                          for url in urls)
            # gather the responses, add any exceptions to the list instead of raising
            responses = await asyncio.gather(*coroutines, return_exceptions=True)
        print('get took {:.2f} seconds'.format(time.time() - start))
        return responses

    async def insert(self, session: aiohttp.ClientSession,
                     url: str, data: list=None, headers: dict=None) -> dict:
        """Insert the data in the given url and return the response body as a dict"""
        # catch any exception and add an argument: the resource. This way the caller can always check
        # which exception occurred on which resource
        start = time.time()
        try:
            async with self.semaphore, session.post(url=url, headers=headers, data=data,
                                                    timeout=TIMEOUT) as response:
                result = await response.json()
        except asyncio.TimeoutError as te:
            # TODO: should we retry this request? How many times?
            te.args += (f'timeout on resource: {url}',)
            print(f'timeout on inserting into {url}: {te}')
            raise
        except Exception as e:
            e.args += (f'resource: {url}',)
            print(f'something went wrong inserting into {url}: {e}')
            raise
        print('fetching {} took {:.2f} seconds'.format(url, time.time() - start))
        return result

    async def call_insert(self, session: aiohttp.ClientSession,
                          url: str, data: list, headers: dict=None) -> list:
        """Unpack the data list and insert each data dict into the url"""
        coros = (self.insert(session=session, url=url, data=d, headers=headers) for d in data)
        responses = await asyncio.gather(*coros, return_exceptions=True)
        return responses

    async def post(self, items: list, headers: dict=None) -> list:
        """This coroutine inserts the given data for each url and returns the response bodies of each request.

        Each item in the input list is a dictionary with 3 keys: a url, a list of one or more data dicts and
        optional headers.
        Optionally, the dict includes headers, which will override the overall headers.

        For each dictonary, a list with response bodies is returned.
        """
        urls = []
        for item in items:
            # assuming item is a dictionary
            url = item.get('url')
            urls.append(dict(url=url, data=item.get('data', []), headers=item.get('headers')))

        start = time.time()
        # the session shouldn't be created outside of a coroutine so it needs to be here rather than in __init__
        # see also https://github.com/aio-libs/aiohttp/issues/2473
        async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
            # create coroutines for each url
            coroutines = (self.call_insert(session=session,
                                           url=url.get('url'), data=url.get('data'), headers=url.get('headers'))
                          for url in urls)
            # gather the responses, add any exceptions to the list instead of raising
            responses = await asyncio.gather(*coroutines, return_exceptions=True)
        print('post {:.2f} seconds'.format(time.time() - start))
        return responses

    async def delete_url(self, session: aiohttp.ClientSession, url: str) -> dict:
        start = time.time()
        try:
            async with self.semaphore, session.delete(url=url, timeout=TIMEOUT) as response:
                result = await response.json()
        except asyncio.TimeoutError as te:
            # TODO: should we retry this request? How many times?
            te.args += (f'timeout on resource: {url}',)
            print(f'timeout on deleting {url}: {te}')
            raise
        except Exception as e:
            e.args += (f'resource: {url}',)
            print(f'something went wrong deleting {url}: {e}')
            raise
        print('delete_url {} took {:.2f} seconds'.format(url, time.time() - start))
        return result

    async def delete(self, urls: list, headers: dict=None) -> list:
        """Delete all urls - flat version
        No response headers are returned."""
        start = time.time()
        # the session shouldn't be created outside of a coroutine so it needs to be here rather than in __init__
        # see also https://github.com/aio-libs/aiohttp/issues/2473
        async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
            # create coroutines for each url
            coroutines = (self.delete_url(session=session, url=url) for url in urls)
            # gather the responses, add any exceptions to the list instead of raising
            responses = await asyncio.gather(*coroutines, return_exceptions=True)
        print('delete took {:.2f} seconds'.format(time.time() - start))
        return responses


def main_caller(items: list, headers: dict={}, method: str= 'get'):
    """Set up event loop, run specific request caller with the list of items, close event loop"""
    # stop if method unknown
    if method not in 'get post delete'.split():
        print(f'method {method} not supported')
        return {}
    if not isinstance(items, list):
        # perhaps just a single item given, pack as list
        items = [items]
    # make sure the event loop is always a new one, because we can't reopen an already closed loop and also we don't
    # want to restart the interpreter between calls to parallel.my_method
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    request_caller = RequestCaller(headers)
    if method.lower() == "get":
        future = request_caller.get(items, headers)
    elif method.lower() == 'post':
        future = request_caller.post(items, headers)
    elif method.lower() == 'delete':
        future = request_caller.delete(items, headers)
    else:
        return []

    result = loop.run_until_complete(future)
    loop.close()
    return result

# call the main caller with the appropriate method
get = partial(main_caller, method='get')
post = partial(main_caller, method='post')
delete = partial(main_caller, method='delete')



