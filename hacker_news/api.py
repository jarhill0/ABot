import requests
import json
from .const import BASE_PATH, API_PATH
from .objector import objectify

DEFAULT_LIMIT = 5


class HackerNews:
    def __init__(self, base_path=BASE_PATH):
        self.base_path = base_path

    def _iterate_listing(self, items, limit):
        items = iter(items)
        i = 0
        while limit is None or i < limit:
            try:
                yield self.item(next(items))
            except StopIteration:
                break
            i += 1

    def ask(self, limit=DEFAULT_LIMIT):
        return self._iterate_listing(self.get(API_PATH['ask']), limit)

    def best(self, limit=DEFAULT_LIMIT):
        return self._iterate_listing(self.get(API_PATH['best']), limit)

    def get(self, path):
        response = requests.get('/'.join((self.base_path, path))).content.decode('utf-8')
        return json.loads(response)

    def item(self, id_number):
        return objectify(self.get(API_PATH['item'].format(id=id_number)), self)

    def jobs(self, limit=DEFAULT_LIMIT):
        return self._iterate_listing(self.get(API_PATH['job']), limit)

    def max_item(self):
        return self.get(API_PATH['maxitem'])

    def new(self, limit=DEFAULT_LIMIT):
        return self._iterate_listing(self.get(API_PATH['new']), limit)

    def show(self, limit=DEFAULT_LIMIT):
        return self._iterate_listing(self.get(API_PATH['show']), limit)

    def top(self, limit=DEFAULT_LIMIT):
        return self._iterate_listing(self.get(API_PATH['top']), limit)
