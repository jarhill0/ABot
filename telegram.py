import json
import time

import requests


class Telegram:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot' + token + '/'
        self.max_id = 0

    def get_updates(self):
        # call getUpdates method and parse as JSON
        response = json.loads(
            requests.get(self.url + 'getUpdates', params={'offset': self.max_id}).content.decode('utf-8'))

        # update the maximum update ID
        for item in response['result']:
            if item['update_id'] >= self.max_id:
                self.max_id = item['update_id'] + 1

        return _check_and_return(response)

    def send_message(self, data):

        for i in range(5):
            response = json.loads(requests.post(self.url + 'sendMessage', data=data).content.decode('utf-8'))
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                time.sleep(2)

    def send_photo(self, data):

        for i in range(5):
            response = json.loads(requests.post(self.url + 'sendPhoto', data=data).content.decode('utf-8'))
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                time.sleep(2)


def _check_and_return(data):
    if not data['ok']:
        print(data)
        raise ConnectionRefusedError('Message did not send successfully.')
    else:
        return data
