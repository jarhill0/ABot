import time

import requests

STATS_URL = 'https://api.blockchain.info/stats'
SATOSHI = 100000000


class Update:
    def __init__(self, url, session=None):
        self.url = url
        self.updated = 0
        self.data = None
        self.session = session or requests.Session()

    def update(self):
        try:
            self.data = self.session.get(self.url).json()
        except requests.RequestException:
            return
        self.updated = time.time()

    def get_data(self):
        """Get the data of this update. May return None."""
        if self.data is None or time.time() - self.updated > 60 * 10:
            self.update()
        return self.data


update = Update(STATS_URL)


def btc_message():
    data = update.get_data()
    if data is None:
        return 'Could not get Bitcoin data.'
    price = data.get('market_price_usd', -1)
    fees = data.get('total_fees_btc', 0) / SATOSHI
    fees_usd = fees * price
    transactions = data.get('n_tx', 0)
    if transactions == 0:
        transactions = 1  # avoid zero division
    avg_fee = fees_usd / transactions

    return 'BTC at ${:,.2f} with avg. fees per transaction at ${:,.2f}.'.format(price, avg_fee)
