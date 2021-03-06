All in Python 2.7

## Google search using Selenium
'Use Selenium to enter a search term in Google and recieve the results' - also see 'Google search using requests module' below.

### Usage
Make [the script](google_search_selenium.py) executable (755 will do) and run:

```
./google_search_selenium.py > google_search_selenium.out
```

Chrome is started and you can see the keystrokes being sent.

### Selenium
Installed Selenium 2.46.0 using pip:

```
$ pip install selenium
Downloading/unpacking selenium
  Downloading selenium-2.46.0.tar.gz (2.6MB): 2.6MB downloaded
  Running setup.py (path:/tmp/pip-build-73a0k3/selenium/setup.py) egg_info for package selenium
    
Installing collected packages: selenium
  Running setup.py install for selenium
    
Successfully installed selenium
Cleaning up...
```

This seems to be the most up-to-date command reference for Selenium: http://release.seleniumhq.org/selenium-core/1.0.1/reference.html

I am following http://selenium.googlecode.com/git/docs/api/py/index.html

### chromedriver
Separate drivers are needed to run Selenium scripts in Chrome or IE. Selenium has native support for Firefox, so no separate driver is needed. Also check: http://stackoverflow.com/questions/21878900/why-do-we-need-iedriver-and-chromedriver-but-no-firefox-driver

I installed chromedriver using https://sites.google.com/a/chromium.org/chromedriver/getting-started. I already had Google Chrome installed (not Chromium!). I chose not to use the Ubuntu packaged chromedriver (apt-cache showpkg chromium-chromedriver) because I'm not sure that's the latest. I downloaded http://chromedriver.storage.googleapis.com/2.16/chromedriver_linux64.zip and unzipped in my home bin dir. This dir is on my PATH (important!).

Running

```
browser = webdriver.Chrome()
```

successfully opens Chrome with the page 'data:,' opened (a blank page).

### Issues
I included a simple sleep statement to give Google and the browser some time to respond. If I don't, the script will print the browser title and page source before it gets a chance to change to the results page.

### Things to consider
As with google_search_requests.py below.
When writing this script, I learnt that Selenium isn't as simple as this script. The docs aren't always very clear (or _done_). I should probably find some course somewhere to learn how to use Selenium to its full extent.


## Google search using requests module
I was asked to "use Python and the requests module to enter a search term in Google and recieve the results" for a job application. Thanks to mr. Lutterop for asking this question.

I have interpreted this question in the simplest way possible. The script ([google_search_requests.py](google_search_requests.py)), which runs command line (see below), asks the user for a search term, uses the requests module to send a get request with that term to Google and print the results as plain text.

### Usage
Make the script executable (chmod 755 google_search_requests.py) and run:

```
./google_search_requests.py
```

Here's an alternative:

```
./google_search_requests.py your search terms > response.txt
```

Use this if you'd like to pipe, because obviously user input doesn't work in that case.

### Issues
When writing this script, I ran into 2 rather inconvenient issues.

#### 1. Temporary failure in name resolution
The get request threw me an error:

```
>>> import requests
>>> payload = {'q': 'french taunting'}
>>> r = requests.get("http://www.google.nl/search", params=payload)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python2.7/dist-packages/requests/api.py", line 60, in get
    return request('get', url, **kwargs)
  File "/usr/lib/python2.7/dist-packages/requests/api.py", line 49, in request
    return session.request(method=method, url=url, **kwargs)
  File "/usr/lib/python2.7/dist-packages/requests/sessions.py", line 457, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/lib/python2.7/dist-packages/requests/sessions.py", line 569, in send
    r = adapter.send(request, **kwargs)
  File "/usr/lib/python2.7/dist-packages/requests/adapters.py", line 407, in send
    raise ConnectionError(err, request=request)
requests.exceptions.ConnectionError: ('Connection aborted.', gaierror(-3, 'Temporary failure in name resolution'))
```

I was unable to reproduce. I'm pretty sure a DNS lookup fail was caused by a briefly interrupted internet connection.

#### 2. The known Python encoding hell
Pyhton outputs using ascii. This can be a problem with certain terminal emulators, apparently including mine. Here's what happens: when you print something to stdout, everything is fine untill you try to pipe that output. This is because Python auto-detects the correct output encoding but not when piping. What worked for me was explicitly telling Python to use utf-8 by adding to my bashrc:

```
export PYTHONIOENCODING=utf-8
```

### Things to consider
I wrote the simplest version of this exercise as possible. However...

- I wrote and tested on Kubuntu 15.04, Python 2.7.9, requests 2.4.3 (was what pip installed)
- There is a Google API out there for this.
- The requests module has response options such as JSON or streaming. Could be useful.
- I am not checking the user input/command line args. Ouch!
- I am also not checking for any errors. Not any.
- The script is command line. I could have created a simple GUI or web page?
- No auth is needed for a Google search, but the user agent has to be correct or Google will refuse the request. It works with the default, so I did not look into the details of user agents. So far, Google didn't block me nor did I get any captchas or whatever.
- I can use event hooks with the get request, which seems interesting.
- I could parse the html output into something readable. But I have to say that using BeatifulSoup4 to parse a Google search results page would be a completely different exercise. Or maybe just prettify the html soup, at request. Note: Google sometimes changes the results page html, breaking the parser.
- On the topic of parsing: probably someone already did this. For example the xgoogle module.
