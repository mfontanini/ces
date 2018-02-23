# Copyright (c) 2018, Matias Fontanini
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

import requests
import threading
import json
from exceptions import *
from utils import CoinPrice

class CoinMetadata:
    def __init__(self, name, price, rank, volume_24h, market_cap, available_supply, total_supply,
                 max_supply, change_1h, change_24h, change_7d):
        self.name = name
        self.price = price
        self.rank = rank
        self.volume_24h = volume_24h
        self.market_cap = market_cap
        self.available_supply = available_supply
        self.total_supply = total_supply
        self.max_supply = max_supply
        self.change_1h = change_1h
        self.change_24h = change_24h
        self.change_7d = change_7d

class CoinDatabase:
    CMC_URL = 'https://api.coinmarketcap.com/v1/ticker/?convert={0}'
    VALID_FIAT_CURRENCIES = set([
        'aud', 'brl', 'cad', 'chf', 'clp', 'cny', 'czk', 'dkk', 'eur', 'gbp', 'hkd', 'huf', 'idr',
        'ils', 'inr', 'jpy', 'krw', 'mxn', 'myr', 'nok', 'nzd', 'php', 'pkr', 'pln', 'rub', 'sek',
        'sgd', 'thb', 'try', 'twd', 'zar', 'usd'
    ])

    def __init__(self, fiat_currency):
        self.fiat_currency = fiat_currency.lower()
        if self.fiat_currency not in CoinDatabase.VALID_FIAT_CURRENCIES:
            raise ConfigException('Unknown fiat currency "{0}"'.format(fiat_currency))
        self._running = True
        self._metadata = {}
        self._metadata_condition = threading.Condition()
        self._stop_condition = threading.Condition()
        self._url = CoinDatabase.CMC_URL.format(self.fiat_currency.upper())
        self._update_thread = threading.Thread(target=self.poll_data)
        self._update_thread.start()

    def stop(self):
        self._running = False
        with self._stop_condition:
            self._stop_condition.notify()
        self._update_thread.join()

    def wait_for_data(self):
        with self._metadata_condition:
            if len(self._metadata) == 0:
                self._metadata_condition.wait()

    def get_currency_price(self, code):
        if self.has_coin(code):
            price = self.get_currency_metadata(code).price
            return CoinPrice(code, price, self.fiat_currency)
        else:
            return CoinPrice(code)


    def get_currency_metadata(self, code):
        with self._metadata_condition:
            if code in self._metadata:
                return self._metadata[code]
            else:
                raise UnknownCurrencyException(code)

    def has_coin(self, code):
        with self._metadata_condition:
            return code in self._metadata

    def poll_data(self):
        while self._running:
            result = None
            try:
                raw_result = requests.get(self._url)
                result = json.loads(raw_result.text)
            except Exception as ex:
                # TODO: somehow log this
                pass
            if result is not None:
                extract_float = lambda i: None if i is None else float(i)
                with self._metadata_condition:
                    for entry in result:
                        try:
                            self._metadata[entry['symbol']] = CoinMetadata(
                                entry['name'],
                                extract_float(entry['price_' + self.fiat_currency]),
                                int(entry['rank']),
                                extract_float(entry['24h_volume_' + self.fiat_currency]),
                                extract_float(entry['market_cap_' + self.fiat_currency]),
                                extract_float(entry['available_supply']),
                                extract_float(entry['total_supply']),
                                extract_float(entry['max_supply']),
                                extract_float(entry['percent_change_1h']),
                                extract_float(entry['percent_change_24h']),
                                extract_float(entry['percent_change_7d'])
                            )
                        except Exception as ex:
                            if 'symbol' in entry:
                                print 'Failed to parse metadata for "{0}": {1}'.format(
                                    entry['symbol'],
                                    ex
                                )
                            else:
                                print 'Failed to parse currency metadata: {0}'.format(ex)
                    self._metadata_condition.notify_all()
            with self._stop_condition:
                # Sleep for 5 minutes
                self._stop_condition.wait(60 * 5)

