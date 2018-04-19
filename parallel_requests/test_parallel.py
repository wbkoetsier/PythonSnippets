from parallel_requests import parallel
import time
import sys
import requests
import mimesis
from mimesis.schema import Field, Schema
from typing import List

mim_field_nl = Field('en-gb')
mim = mimesis.Generic('en-gb')


def mock_persons(n: int = 1) -> List[dict]:
    """Return a list of persons according to schema
    Schema is beta. We can't pass arguments, so add birthday and tag separately."""
    schema = Schema(schema=(
        lambda: {
            'firstname': mim_field_nl('person.name'),
            'lastname': mim_field_nl('person.last_name'),
        }
    ))
    persons = schema.create(n)
    if isinstance(persons, dict):
        persons = [persons]
    # include sensible birth date
    persons = [dict(p, birthdate=mim.datetime.date(start=1940, end=2000, fmt='%Y-%m-%d')) for p in persons]
    # include tag: the person's name (initials)
    persons = [dict(p, tag=f"{p['firstname'][0]}{p['lastname']}".replace(' ', '').strip().lower())
               for p in persons]
    print('persons:', persons)
    return persons

if __name__ == '__main__':

    # ## parallel delete
    # start = time.time()
    # urls = []
    # for item in requests.get('https://demo.yourapi.io/playground/dynamic/student', params={'limit': 10}).json():
    #     urls.append(item.get('_href_'))
    # print('fetching the list of students in sync took {:.2f} seconds'.format(time.time() - start))
    # start = time.time()
    # parallel.delete(urls)
    # print('deleting 1000+ records from students took {:.2f} seconds'.format(time.time() - start))
    # sys.exit()

    # ## parallel insert
    # domain = 'static'
    #
    # n_students = 10
    # start = time.time()
    # for student in mock_persons(n_students):
    #     r = requests.post(url='https://demo.yourapi.io/playground/dynamic/student',
    #                       data=student)
    #     print(r.status_code)
    # print('filling playground with {} students in sync took {:.2f} seconds'.format(n_students, time.time() - start))
    #
    # start = time.time()
    #
    # parallel.post(dict(url='https://demo.yourapi.io/playground/dynamic/student',
    #                    data=mock_persons(n_students)))
    # print('filling playground with {} students in parallel took {:.2f} seconds'.format(n_students, time.time() - start))
    # sys.exit()

    ## parallel get
    # the below tests functionality of parallel get

    # d0: prove that asyncio.gather preserves sort order, despite different results arrival
    # https://docs.python.org/3/library/asyncio-task.html#asyncio.gather
    d0 = 'https://demo.yourapi.io/playground/dynamic/student?limit=10'
    rp0 = parallel.get(d0)
    rs0 = []
    for s in requests.get(d0).json():
        result = requests.get(s.get('_href_')).json()
        result['_timestamp_'] = str(result['_timestamp_'])
        result['_id_'] = str(result['_id_'])
        rs0.append(result)
    # the result should be the same: sort order preserved
    print(rp0[0] == rs0)

    sys.exit()

    # d2: the item is a dict
    d2 = dict(url='https://demo.yourapi.io/playground/static/student/bccad8ad-ade3-4e46-a20c-f93c5bda7e7b/firstname')
    # d3: let's also pass params, even though the url has params and see the params dict ignored
    d3 = dict(url='https://demo.yourapi.io/playground/static/student?limit=3', params=dict(limit=5))
    # d4: the item is a single url as a string but the response is biiig (I have 1000+ students in draft static)
    d4 = 'https://demo.yourapi.io/playground/static/student?limit=-1'
    # d5: perhaps you wish to just pass the urls from result of a get (list)
    d5 = [s.get('_href_') for s in requests.get('https://demo.yourapi.io/playground/static/student').json()]
    # d6: or better: don't bother about unpacking those urls
    d6 = requests.get('https://demo.yourapi.io/playground/static/student').json()

    start = time.time()
    r = parallel.get([d2, d3, d4] + d5 + d6)
    print('all these calls combined took {:.2f} seconds'.format(time.time() - start))
    print('-'*25, f'\nfinal results: {len(r)} items')
    for i in range(len(r)):
        if isinstance(r[i], list):
            print(f'item {i} is a list with {len(r[i])} items')
            for j in r[i]:
                print('\t', j)
        else:
            print(f'item {i} is a single item: {r[i]}')

    # this older code still works, and it also shows that we can call parallel get multiple times without
    # running into problems with closed event loops
    print('-'*25, '\nlast parallel call')
    res = requests.get('https://demo.yourapi.io/playground/static/student?limit=10000')
    students = res.json()
    print(len(students))

    start = time.time()
    students_full = parallel.get([s.get('_href_') for s in students])
    print('this last call using parallel get took {:.2f} seconds'.format(time.time() - start))

    for student in students_full:
        if isinstance(student, dict):
            print(student.get('firstname'), student.get('lastname'), student.get('subjects'))
        else:
            print(student)

    # and now sync:
    print('-' * 25, '\nretry this in sync')  # my 1050 students take ~45 seconds
    start = time.time()
    for student in students:
        print(requests.get(student.get('_href_')))
    print('calling the same amount of students in sync took {:.2f} seconds'.format(time.time() - start))

    # https://medium.com/python-pandemonium/asyncio-coroutine-patterns-beyond-await-a6121486656f
    # https://snarky.ca/how-the-heck-does-async-await-work-in-python-3-5/
    # https://hackernoon.com/asyncio-for-the-working-python-developer-5c468e6e2e8e

