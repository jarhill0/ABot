import os
import json


def folder_path():
    return os.path.dirname(os.path.abspath(__file__))


class SubscriptionNotFoundError(Exception):
    pass


class Subscriptions:
    saved_subs_path = os.path.join(folder_path(), 'data', 'subscriptions.json')

    def __init__(self, keys):
        self.subs = dict()

        try:
            with open(Subscriptions.saved_subs_path) as f:
                saved_subs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            saved_subs = dict()
            self.subs = saved_subs  # preserves previously saved keys/lists even if not names in init params

        for key in keys:
            if key not in self.subs.keys():
                self.subs[key] = set([])

        self._update_saved_copy()

    def __repr__(self):
        return repr(self.subs)

    def _update_saved_copy(self):
        list_subs = dict()
        for key, value in zip(self.subs.keys(), self.subs.values()):
            list_subs[key] = list(value)
        with open(Subscriptions.saved_subs_path, 'w') as f:
            json.dump(list_subs, f)

    def subscribe(self, list_id, chat_id):
        if list_id not in self.subs.keys():
            raise SubscriptionNotFoundError
        self.subs[list_id].add(chat_id)
        self._update_saved_copy()

    def unsubscribe(self, list_id, chat_id):
        if list_id not in self.subs.keys():
            raise SubscriptionNotFoundError
        if chat_id in self.subs[list_id]:
            self.subs[list_id].remove(chat_id)
            self._update_saved_copy()

    def get_subscribers(self, list_id):
        if list_id not in self.subs.keys():
            raise SubscriptionNotFoundError
        for subscriber in self.subs[list_id]:
            yield subscriber
