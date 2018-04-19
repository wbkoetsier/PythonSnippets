#!/usr/bin/python
# WBKoetsier 9Jul2015

# very short script that uses selenium to fire up Google Chrome, get the
# Google search page, send a search term and print the full plain text
# html to stdout.

# install selenium: pip install selenium
# get the Chrome driver: http://chromedriver.storage.googleapis.com/2.16/chromedriver_linux64.zip unzipped in my ~/bin, which is already on the PATH


# imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep

# fire up Chrome
browser = webdriver.Chrome()

# navigate to https://www.google.com (this opens the url with the gfe_rd and ei parameters)
browser.get('https://www.google.com')

# check if the word 'Google' is in the title (returns nothing on success)
assert 'Google' in browser.title

# no, in stead, print title to stdout
print 'Browser title before submitting search term:', browser.title

# the assert test is aborted if the text isn't found:
#>>> assert 'foo' in browser.title
#Traceback (most recent call last):
#  File "<stdin>", line 1, in <module>
#AssertionError
# catch/use the AssertionError in a real world script.

# find the search box
# the search box is an input field with the name 'q'. For example, use browser devtools
# to find the search box input element. This also tells me there is only one element
# that has name="q".
searchboxelement = browser.find_element_by_name('q') # finds first element with name attribute value = q

# use Keys to send keystrokes to the search box element: a search term and hit the return key to submit
searchboxelement.send_keys('elderberry' + Keys.RETURN)

# now give Google some time to respond and give the browser some time too!
sleep(5) # bit long perhaps, doesn't matter

# check results
print 'Browser title after submitting search term:', browser.title

# use one of the available methods to access the elements of the resulting page, for example use xpath.
# or stay with the google_search_requests.py script, print the full plain text html to stdout.
print 'Page source:'
print browser.page_source

# always close browser to clean up.
browser.quit()
