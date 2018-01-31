import copy
import time

import requests


class Telegram:
    def __init__(self, token):
        self.token = token
        self.url = 'https://api.telegram.org/bot' + self.token + '/'
        self.max_id = 0
        self.rates = dict()

    def __repr__(self):
        return 'Telegram({})'.format(self.token)

    @staticmethod
    def make_submessages(base_message):
        """Take a message object and return multiple with commands split"""
        orig_text = base_message['text']
        del base_message['text']
        orig_entities = base_message['entities']
        bot_commands = [e for e in orig_entities if e['type'] == 'bot_command']
        del base_message['entities']

        splits = [e['offset'] for e in bot_commands] + [len(orig_text)]
        submessages = []

        end = splits.pop(0)
        while len(splits) > 0:
            mess = copy.deepcopy(base_message)

            start = end
            end = splits.pop(0)
            mess['text'] = orig_text[start:end]

            mess_ents = []
            for ent in orig_entities:
                if start <= ent['offset'] and ent['offset'] + ent['length'] < end:
                    mess_ents.append(copy.copy(ent))
                    mess_ents[-1]['offset'] -= start  # offset shifts when we modify text
            mess['entities'] = mess_ents

            submessages.append(mess)

        return submessages

    def get_updates(self):
        # call getUpdates method and parse as JSON
        response = requests.get(self.url + 'getUpdates', params={'offset': self.max_id, 'timeout': 30}).json()

        # update the maximum update ID
        for item in response['result']:
            if item['update_id'] >= self.max_id:
                self.max_id = item['update_id'] + 1

        return _check_and_return(response)

    def send_message(self, data):
        datae = []
        while len(data['text']) > 4000:
            temp = data.copy()
            temp['text'] = data['text'][:4000]
            data['text'] = data['text'][4000:]
            datae.append(temp)
        datae.append(data)

        responses = []

        for data_ in datae:
            for i in range(2):
                response = requests.post(self.url + 'sendMessage', data=data_).json()
                try:
                    responses.append(_check_and_return(response))
                except ConnectionRefusedError:
                    print(data_)
                    if response['error_code'] == 403:
                        break
                    time.sleep(2)
                else:
                    break

        return responses

    def send_photo(self, data):

        for i in range(2):
            response = requests.post(self.url + 'sendPhoto', data=data).json()
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                print(data)
                time.sleep(2)

    def send_video(self, data):
        for i in range(2):
            response = requests.post(self.url + 'sendVideo', data=data).json()
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                print(data)
                time.sleep(2)

    def delete_message(self, data):
        for i in range(2):
            response = requests.post(self.url + 'deleteMessage', data=data).json()
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

    def get_me(self):
        response = requests.get(self.url + 'getMe').json()
        return response

    def set_chat_title(self, data):
        for i in range(2):
            response = requests.post(self.url + 'setChatTitle', data=data).json()
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                print(data)
                time.sleep(2)

    def get_chat(self, data):
        for i in range(2):
            response = requests.post(self.url + 'getChat', data=data).json()
            try:
                return _check_and_return(response)
            except ConnectionRefusedError:
                print(data)
                time.sleep(2)


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
