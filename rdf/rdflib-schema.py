import requests
from rdflib import ConjunctiveGraph
import json

"""Short snippet to parse schema.org graph"""


TYPE = 'http://schema.org/EmailMessage'

if __name__ == '__main__':

    schema = requests.get(f'{TYPE}.jsonld')

    # http://rdflib.readthedocs.io/en/stable/index.html
    g = ConjunctiveGraph()
    print(g, len(g))  # an empty ConjunctiveGraph object
    g.parse(data=json.dumps(schema), format='application/ld+json')
    print(len(g))  # 5 triples for EmailMessage, 894 for Message

    for subj, pred, obj in g:
        print(f'subject: {subj}, predicate: {pred}, object: {obj}')

