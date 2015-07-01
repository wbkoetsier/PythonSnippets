#!/usr/bin/python
# WBKoetsier 1Jul2015

# This short script asks the user for a search term, uses the requests
# module to send a get request to Google search and prints the full
# plain text html to stdout.
# For more information and some considerations, see the README in
# https://github.com/wbkoetsier/PythonExercises

# usage:
# This script runs command line, was written and tested on Kubuntu 15.04,
# Python 2.7.9 and requests 2.4.3.
# Make the script executable (chmod 755 google_search_requests.py) and run:
# ./google_search_requests.py
# However... If you, like me, don't like output spilling all over your
# terminal window and would like to pipe output to less or file, you can
# simply type the search term as comand line options.
# ./google_search_requests.py french taunting


# imports: really, we only need requests
import requests
# OK, for args for piping then.
import sys
# And for pretty printing the response.
from bs4 import BeautifulSoup

# start with empty string for search term
searchterm = str()

# check for args, if present, use the total as search term.
# no arguments? ask user for search term(s)
if len(sys.argv) >= 2:
    searchterm = ' '.join(sys.argv[1:])
else:
    searchterm = raw_input('Type your search string: ')

print 'You entered the following search term:', searchterm

# this is the most basic Google search url:
url = 'https://www.google.nl/search'

# using only the q parameter, the get request payload will be:
payload = {'q': searchterm}

# the get request
r = requests.get(url, params=payload)

# short feedback to the user:
print 'Get request done using url:', r.url

# we could give some more feedback, for example:
#print 'Google returns content type', r.headers['content-type']

# we could use bs4 to parse the response
soup = BeautifulSoup(r.text)
# and then find an efficient method for finding the titles, urls and
# descriptions using bs4
#soup.find_all('li', class_='g')
# or just pretty print.

print 'Response prettified below:'
print soup.prettify()
# or just print r.text