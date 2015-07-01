# PythonExercises
Python exercises to improve my skills

## Google search using requests module
I was asked to "use Python and the requests module to enter a search term in Google and recieve the results" for a job application. Thanks to mr. Lutterop for asking this question.

I have interpreted this question in the simplest way possible. The script, which runs command line (see below), asks the user for a search term, uses the requests module to send a get request with that term to Google and print the results as plain text.

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
