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
import json
from binance.client import Client
from crypto_exchange_shell.models import *
from crypto_exchange_shell.exceptions import *
from crypto_exchange_shell.exchanges.base_exchange_wrapper import BaseExchangeWrapper

class BinanceWrapper(BaseExchangeWrapper):
    def __init__(self, api_key, api_secret):
        BaseExchangeWrapper.__init__(self)
        self._handle = Client(api_key, api_secret)
        self._load_markets()

    def _perform_request(self, request_lambda):
        try:
            return request_lambda()
        except Exception as ex:
            raise ExchangeAPIException(ex.message)

    def _load_names(self):
        try:
            result = requests.get('https://api.coinmarketcap.com/v1/ticker/')
            data = json.loads(result.text)
        except Exception as ex:
            print 'Failed to parse coinmarketcap data: {0}'.format(ex)
        names = {}
        for item in data:
            names[item['symbol']] = item['name']
        return names

    def _make_exchange_name(self, base_currency_code, market_currency_code):
        return '{0}{1}'.format(market_currency_code, base_currency_code)

    def _load_markets(self):
        names = self._load_names()
        result = self._perform_request(lambda: self._handle.get_exchange_info())
        for symbol in result['symbols']:
            base_currency = symbol['quoteAsset']
            market_currency = symbol['baseAsset']
            self.add_currency(
                Currency(base_currency, names.get(base_currency, base_currency), 0, 0)
            )
            self.add_currency(
                Currency(market_currency, names.get(market_currency, market_currency), 0, 0)
            )
            self.add_market(base_currency, market_currency)

    def get_currency(self, currency_code):
        if currency_code not in self._currencies:
            raise InvalidArgumentException('Invalid currency {0}'.format(currency_code))
        return self._currencies[currency_code]

    def get_market_state(self, base_currency_code, market_currency_code):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.get_all_tickers())
        price = None
        for entry in result:
            if entry['symbol'] == exchange_name:
                price = entry['price']
        if price is not None:
            result = self._handle.get_orderbook_tickers()
            for entry in result:
                if entry['symbol'] == exchange_name:
                    return MarketState(
                        float(entry['askPrice']),
                        float(entry['bidPrice']),
                        float(price)
                    )
        raise ExchangeAPIException('Failed to fetch information for given market')

    def get_orderbook(self, base_currency_code, market_currency_code):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.get_order_book(symbol=exchange_name))
        buy_orderbook = Orderbook()
        sell_orderbook = Orderbook()
        for item in result['bids']:
            buy_orderbook.add_order(Order(float(item[0]), float(item[1])))
        for item in result['asks']:
            sell_orderbook.add_order(Order(float(item[0]), float(item[1])))
        return (buy_orderbook, sell_orderbook)

    def get_wallets(self):
        result = self._perform_request(lambda: self._handle.get_account())
        output = []
        for data in result['balances']:
            currency = data['asset']
            # Shouldn't happen. TODO: log this
            if currency not in self._currencies:
                continue
            free = float(data['free'])
            locked = float(data['locked'])
            wallet = Wallet(
                self._currencies[currency],
                free + locked,
                free,
                locked
            )
            output.append(wallet)
        return output

    def get_wallet(self, currency_code):
        result = self._perform_request(lambda: self._handle.get_asset_balance(currency_code))
        free = float(result['free'])
        locked = float(result['locked'])
        return Wallet(
            self._currencies[currency_code],
            free + locked,
            free,
            locked
        )

    def buy(self, base_currency_code, market_currency_code, amount, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.order_limit_buy(symbol=exchange_name,
                                                                            quantity=amount,
                                                                            price=rate))
        return result['clientOrderId']

    def sell(self, base_currency_code, market_currency_code, amount, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.order_limit_sell(symbol=exchange_name,
                                                                             quantity=amount,
                                                                             price=rate))
        return result['clientOrderId']

    def get_deposit_address(self, currency_code):
        result = self._perform_request(lambda: self._handle.get_deposit_address(asset=currency_code))
        return CryptoAddress(
            currency_code,
            result['address'],
            result.get('addresTag', None)
        )
