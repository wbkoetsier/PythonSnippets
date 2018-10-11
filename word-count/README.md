# Wikipedia word count

## Introduction
This is an assignment I was given for a job application. The goal is simple: what is the top 10 most used words on some
(randomly chosen) Wikipedia pages? Performance should be optimal.

## Approach
Here's some thoughts I was having during the interview, when I was asked if I could do this for them.
- Fetch the data in parallel, if Python 3.5 or 3.6 (aiohttp). I already have code for that.
- Does Wikipedia have an API? - Yes it does: https://www.mediawiki.org/wiki/API:Main_page
- I have options: parallel vs sync, scraping vs. API, implement word count vs word count API.

I'll start out with a simple word count on some pages using the Wikipedia API, no optimisation yet.

## Requirements
I used Python 3.6
- `requests`
- `mwparserfromhell` (https://github.com/earwig/mwparserfromhell)

- As for usage of `str.translate` (and `str.maketrans`): Python version must be 3.
- As for usage of type hinting, Python must be 3.5+.




