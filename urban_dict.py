import json

import requests

API_PATH = 'http://api.urbandictionary.com/v0/define'


def build_message(term):
    ud_response = json.loads(requests.get(API_PATH, params={'term': term}).content.decode('utf-8'))
    if ud_response['result_type'] != 'exact':  # unknown how many possible responses the API gives here
        return 'No definition found for {}.'.format(term)
    entry = ud_response['list'][0]
    word = entry['word']
    definition = entry['definition']
    example = entry['example']

    return '*{}*:\n{}\n_{}_'.format(word, definition, example)  # Naively assume no special characters in strings
