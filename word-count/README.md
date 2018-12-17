# Wikipedia word count

## Introduction
This is an assignment I was given for a job application. The goal is simple: what is the top 10 most used words on some
(randomly chosen) Wikipedia pages? Performance should be optimal.

## Usage
Just run main as is for both versions. Requires Python 3.6, `requests`, `mwparserfromhell`.

## Approach
### v1
I'll start out with a simple word count on some pages using the Wikipedia API.
- Python 3.6, which is what I'm most familiar with. I'm also very fond of f-strings and type hinting.
- Use the [WikiMedia API](https://www.mediawiki.org/wiki/API:Main_page) to fetch page contents. There are some
  possibilities to do this, using `action=query` or `action=parse`. Each method has it's own quirks. For example, to
  get plain text, you can use `action=query` with `prop=extracts` and `explaintext=true`. However, the idea of this
  method is to extract just the first section of the page. Using `action=parse` I could get HTML results and parse that
  using [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) (it's actually quite trivial to extract
  just the text contents from HTML soup). I ended up using the query action with revisions property, limiting to the
  contents of 1 revision. This returns the contents in mediawiki format, which can easily be parsed using the
  [mwparserfromhell](https://github.com/earwig/mwparserfromhell).
- Make synchronous requests using `requests`.
- Use `collections.Counter` for word count. It makes getting the most common words trivial and it would seems that it's
  also already very efficient.
- Use `str.translation` with `str.maketrans` to get rid of special characters in the text (I don't want to count, say,
  `/` or `(and`). From a quick glance on Google (SO threads, mainly), this seems to be more efficient than for example
  `str.replace` or `re.sub`.
- Write a manual, random list of page titles.

### Ideas for additional versions
- Speed up fetching pages.
  - Replace the manual title list with a query (for example, 'find me all page titles for pages about Monty Python' or
    '...for pages starting with M' or such, or even by geographic location) on the API. This way, I can run it for many
    more pages.
    - Would probably require the query action with `list` or `generator` search option.
  - See how to use the API's `generator` output and `continue` (in whatever form), it might be useful for speeding up.
  - Parallelise the requests using my `parallel_requests` code (aiohttp using async/await syntax, Python 3.5+).
    - How does this play with the API's generator?
    - Should I parse contents directly after the request, or at a different point?
  - Is the mw parser from hell the most efficient? I could benchmark using several mw parsers, or also include fetching
    pages as HTML and parse using BeautifulSoup4.
- Speed up word count.
  - Benchmark the usage of `Counter`.
  - Benchmark the use of `str.translate`.
  - I suspect these 2 are already among the most efficient solutions when parsing significant amounts of data.
  - Atm, I loop over all pages to concatenate the texts into one large string. If I were to fetch many more pages, that
  would be inefficient. I could find a way to parallelise that using async/await syntax. Or look into counting per page
  and then zipping the counts for all pages into one count.

Other things I could consider:
- Use a Wikipedia database. There's a [dump that can be downloaded](https://en.wikipedia.org/wiki/Wikipedia:Database_download#Why_not_just_retrieve_data_from_wikipedia.org_at_runtime?),
  or there's DBpedia. What would be most efficient? If I wanted to, I could do map/reduce kind of stuff...
- As a showcase, I could write my own most common word counter. It would involve efficiently sorting the list of words.
- On a simpler note, I could make a version that works on Python 3.4, or on Python 2.7.
- Look into using Pandas or numpy, would these be helpful when counting the most common words among a great many of
  Wikipedia pages?

### v2: async/await and aiohttp
Using `aiohttp==3.4.4` and Python 3.6.

I've also added a timer to the version 1, so the versions can be compared.


## Requirements
Python version: 3.6

Install packages:
- `requests`
- `mwparserfromhell` (https://github.com/earwig/mwparserfromhell)

### Minimal Python versions for features
- `str.translate` (and `str.maketrans`): Python 3.
- Type hinting: Python 3.5+.
- f-strings (`f'some {var}'`): Python 3.6+.




