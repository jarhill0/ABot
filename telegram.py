import json
import time

import requests


class Telegram:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot' + token + '/'
        self.max_id = 0
        self.rates = dict()

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
        datae = []
        while len(data['text']) > 4000:
            temp = data.copy()
            temp['text'] = data['text'][4000:]
            datae.append(temp)
        datae.append(data)

        for data in datae:
            for i in range(5):
                response = json.loads(requests.post(self.url + 'sendMessage', data=data).content.decode('utf-8'))
                try:
                    return _check_and_return(response)
                except ConnectionRefusedError:
                    print(data)
                    if response['error_code'] == 403:
                        break

                    time.sleep(2)

    def send_photo(self, data):

        for i in range(5):
            response = json.loads(requests.post(self.url + 'sendPhoto', data=data).content.decode('utf-8'))
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                print(data)
                time.sleep(2)

    def is_limited(self, id_number):
        now = time.time()

        if id_number not in self.rates.keys():
            self.rates[id_number] = [now, ]
            return False
        else:
            times = self.rates[id_number]  # direct reference to the actual list; modifications hold
            if len(times) < 10:
                # if fewer than 10 messages sent to that chat on record, no rate limiting.
                times.append(now)
                return False
            else:
                if now - times[0] >= 60:
                    # if the time since the tenth message is more than a minute, update the list and post message
                    del times[0]
                    times.append(now)
                    return False
                else:
                    # if the time since the tenth message is less than a minute, this message will not be sent, so do
                    # not update the times list
                    return True


def _check_and_return(data):
    if not data['ok']:
        print(data)
        raise ConnectionRefusedError('Message did not send successfully.')
    else:
        return data


def user_name(user):
    if 'username' in user.keys():
        return '@' + user['username']
    else:
        name = user['first_name']
        if 'last_name' in user.keys():
            name += ' ' + user['last_name']
        return name
