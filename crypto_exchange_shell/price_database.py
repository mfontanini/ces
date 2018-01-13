import requests
import threading
import json
from exceptions import *

class PriceDatabase:
    CMC_URL = 'https://api.coinmarketcap.com/v1/ticker/'

    def __init__(self, convert=None):
        self._convert = convert
        self._running = True
        self._price_key = 'price_usd'
        self._prices = {}
        self._prices_condition = threading.Condition()
        self._stop_condition = threading.Condition()
        self._update_thread = threading.Thread(target=self.poll_prices)
        self._update_thread.start()

    def stop(self):
        self._running = False
        with self._stop_condition:
            self._stop_condition.notify()
        self._update_thread.join()

    def wait_for_data(self):
        with self._prices_condition:
            if len(self._prices) == 0:
                self._prices_condition.wait()

    def get_currency_price(self, code):
        with self._prices_condition:
            if code in self._prices:
                return self._prices[code]
            else:
                raise UnknownCurrencyException(code)

    def poll_prices(self):
        while self._running:
            result = None
            try:
                raw_result = requests.get(PriceDatabase.CMC_URL)
                result = json.loads(raw_result.text)
            except Exception as ex:
                print "Failed to load currency prices: {0}".format(ex)
            if result is not None:
                with self._prices_condition:
                    for entry in result:
                        self._prices[entry['symbol']] = float(entry[self._price_key])
                    self._prices_condition.notify_all()
            with self._stop_condition:
                # Sleep for 5 minutes
                self._stop_condition.wait(60 * 5)

