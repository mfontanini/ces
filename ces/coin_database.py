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
import re
from exceptions import *
from utils import CoinPrice

class CoinMetadata:
    def __init__(self, code, name, price, rank, volume_24h, market_cap, available_supply,
                 total_supply, max_supply, change_1h, change_24h, change_7d):
        self.code = code
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
    API_URL = 'https://api.coinmarketcap.com/v1/ticker/?convert={0}'
    WEB_URL = 'https://coinmarketcap.com/all/views/all/'
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
        self._api_url = CoinDatabase.API_URL.format(self.fiat_currency.upper())
        self._web_url = CoinDatabase.WEB_URL
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

    def get_top_coins(self, top_limit):
        coins = []
        with self._metadata_condition:
            for coin in self._metadata.values():
                if coin.rank is not None and coin.rank <= top_limit:
                    coins.append(coin)
        return sorted(coins, key=lambda i: i.rank)

    def _extract_float(self, value):
        return None if value is None else float(value)

    def _merge_attribute(self, lhs, rhs, attribute):
        if getattr(rhs, attribute) is not None:
            setattr(lhs, attribute, getattr(rhs, attribute))    

    def _add_coin(self, code, coin):
        if code in self._metadata:
            stored_coin = self._metadata[code]
            self._merge_attribute(stored_coin, coin, "name")
            self._merge_attribute(stored_coin, coin, "price")
            self._merge_attribute(stored_coin, coin, "rank")
            self._merge_attribute(stored_coin, coin, "volume_24h")
            self._merge_attribute(stored_coin, coin, "market_cap")
            self._merge_attribute(stored_coin, coin, "available_supply")
            self._merge_attribute(stored_coin, coin, "total_supply")
            self._merge_attribute(stored_coin, coin, "max_supply")
            self._merge_attribute(stored_coin, coin, "change_1h")
            self._merge_attribute(stored_coin, coin, "change_24h")
            self._merge_attribute(stored_coin, coin, "change_7d")
        else:
            self._metadata[code] = coin

    def _load_from_api(self):
        result = None
        try:
            raw_result = requests.get(self._api_url)
            result = json.loads(raw_result.text)
        except Exception as ex:
            # TODO: somehow log this
            pass
        if result is not None:
            with self._metadata_condition:
                for entry in result:
                    try:
                        coin = CoinMetadata(
                            entry['symbol'],
                            entry['name'],
                            self._extract_float(entry['price_' + self.fiat_currency]),
                            int(entry['rank']),
                            self._extract_float(entry['24h_volume_' + self.fiat_currency]),
                            self._extract_float(entry['market_cap_' + self.fiat_currency]),
                            self._extract_float(entry['available_supply']),
                            self._extract_float(entry['total_supply']),
                            self._extract_float(entry['max_supply']),
                            self._extract_float(entry['percent_change_1h']),
                            self._extract_float(entry['percent_change_24h']),
                            self._extract_float(entry['percent_change_7d'])
                        )
                        self._add_coin(entry['symbol'], coin)
                    except Exception as ex:
                        if 'symbol' in entry:
                            print 'Failed to parse metadata for "{0}": {1}'.format(
                                entry['symbol'],
                                ex
                            )
                        else:
                            print 'Failed to parse currency metadata: {0}'.format(ex)
                self._metadata_condition.notify_all()

    def _load_from_web(self):
        if self.fiat_currency == 'usd':
            conversion_rate = 1.0
        else:
            data = requests.get(self._api_url).text
            data = json.loads(data)
            # Find the conversion rate between USD and whatever fiat currency we're using
            for coin in data:
                if coin['symbol'] == 'BTC':
                    conversion_rate = float(coin['price_' + self.fiat_currency]) / float(coin['price_usd'])
        data = requests.get(self._web_url).text
        table_start = data.find('id="currencies-all"')
        table_end = data.find('</table>', table_start)
        table = data[table_start:table_end]
        attribute_keys = {
            'class="text-center">' : 'rank',
            'currency-name-container' : 'name',
            'col-symbol' : 'code',
            'market-cap' : 'market-cap',
            'class="price"' : 'price',
            'circulating-supply' : 'circulating-supply',
            'class="volume"' : 'volume',
            'data-timespan="1h"' : 'change-1h',
            'data-timespan="24h"' : 'change-24h',
            'data-timespan="7d"' : 'change-7d',
        }
        price_attributes = ['price', 'market-cap', 'volume']
        number_attributes = price_attributes + ['circulating-supply']
        percentage_attributes = ['change-1h', 'change-24h', 'change-7d']
        with self._metadata_condition:
            for entry in table.split('<tr ')[1:]:
                attributes = {}
                for column in entry.split('<td '):
                    for key, value in attribute_keys.items():
                        if key in column:
                            index = column.find(key)
                            match = re.findall('>([^<]+)<', column[index:], re.MULTILINE)
                            match = map(lambda i: i.strip(), match)
                            match = filter(lambda i: len(i) > 0, match)
                            if len(match) > 0:
                                attributes[value] = match[0].strip()
                            else:
                                attributes[value] = None
                for key in number_attributes:
                    if attributes.get(key, None):
                        try:
                            attributes[key] = float(attributes[key].replace('$', '').replace(',', ''))
                        except:
                            attributes[key] = None
                for key in price_attributes:
                    if attributes.get(key, None):
                        attributes[key] *= conversion_rate
                for key in percentage_attributes:
                    if attributes.get(key, None):
                        attributes[key] = float(attributes[key].replace('%', ''))
                try:
                    coin = CoinMetadata(
                        attributes['code'],
                        attributes['name'],
                        attributes['price'],
                        int(attributes['rank']),
                        attributes['volume'],
                        attributes['market-cap'],
                        attributes['circulating-supply'],
                        None,
                        None,
                        attributes.get('change-1h', None),
                        attributes.get('change-24h', None),
                        attributes.get('change-7d', None)
                    )
                    self._add_coin(attributes['code'], coin)
                except Exception as ex:
                    pass

    def poll_data(self):
        while self._running:
            # Load all coins by parsing coinmarketcap.com/all/views/all/
            try:
                self._load_from_web()
            except:
                pass
            # Now get some better data for the coins that are served through the API
            self._load_from_api()
            with self._stop_condition:
                # Sleep for 5 minutes
                self._stop_condition.wait(60 * 5)

