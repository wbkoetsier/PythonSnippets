# Wikipedia word count

## Introduction
This is an assignment I was given for a job application. The goal is simple: what is the top 10 most used words on some
(randomly chosen) Wikipedia pages? Performance should be optimal.

## Approach
Some thoughts on approach.
- Fetch the data in parallel, if Python 3.5 or 3.6 (aiohttp). I already have code for that.
- Does Wikipedia have an API?
- I have options: parallel vs sync, scraping vs. API, implement word count vs word count API.

### v1
At commit https://github.com/wbkoetsier/PythonSnippets/commit/86ec289d9abb4dd21e34130b342d82cd3a946152.

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

## Requirements
Python version: 3.6

Install packages:
- `requests`
- `mwparserfromhell` (https://github.com/earwig/mwparserfromhell)

### Minimal Python versions for features
- `str.translate` (and `str.maketrans`): Python 3.
- Type hinting: Python 3.5+.
- f-strings (`f'some {var}'`): Python 3.6+.
- `aiohttp` with `async`/`await` syntax: Python 3.5+




