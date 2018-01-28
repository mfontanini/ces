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
import dateparser
from time import mktime
from datetime import datetime
from binance.client import Client
from crypto_exchange_shell.models import *
from crypto_exchange_shell.exceptions import *
from crypto_exchange_shell.exchanges.base_exchange_wrapper import *
import crypto_exchange_shell.utils as utils

class OrderFilter:
    def __init__(self, min_price, max_price, price_tick, min_amount, max_amount,
                 amount_step, min_notional):
        self.min_price = min_price
        self.max_price = max_price
        self.price_tick = price_tick
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.amount_step = amount_step
        self.min_notional = min_notional

class BinanceWrapper(BaseExchangeWrapper):
    INTERVAL_MAP = {
        CandleTicks.one_minute : Client.KLINE_INTERVAL_1MINUTE,
        CandleTicks.five_minutes : Client.KLINE_INTERVAL_5MINUTE,
        CandleTicks.thirty_minutes : Client.KLINE_INTERVAL_30MINUTE,
        CandleTicks.one_hour : Client.KLINE_INTERVAL_1HOUR,
        CandleTicks.one_day : Client.KLINE_INTERVAL_1DAY,
    }

    def __init__(self, api_key, api_secret):
        BaseExchangeWrapper.__init__(self, exposes_confirmations=False)
        self._handle = Client(api_key, api_secret)
        self._filters = {}
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

    def _split_sumbol(self, symbol):
        for base_code, markets in self._markets.items():
            for market_code in markets:
                if market_code + base_code == symbol:
                    return (base_code, market_code)
        raise ExchangeAPIException('Failed to decode symbol {0}'.format(symbol))

    def _add_filter(self, exchange, filters):
        min_price = None
        max_price = None
        price_tick = None
        min_amount = None
        max_amount = None
        amount_step = None
        min_notional = None
        for f in filters:
            if f['filterType'] == 'PRICE_FILTER':
                min_price = float(f['minPrice'])
                max_price = float(f['maxPrice'])
                price_tick = float(f['tickSize'])
            elif f['filterType'] == 'LOT_SIZE':
                min_amount = float(f['minQty'])
                max_amount = float(f['maxQty'])
                amount_step = float(f['stepSize'])
            elif f['filterType'] == 'MIN_NOTIONAL':
                min_notional = float(f['minNotional'])
        self._filters[exchange] = OrderFilter(
            min_price,
            max_price,
            price_tick,
            min_amount,
            max_amount,
            amount_step,
            min_notional
        )

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
            self._add_filter(symbol['symbol'], symbol['filters'])

    def get_currency(self, currency_code):
        if currency_code not in self._currencies:
            raise InvalidArgumentException('Invalid currency {0}'.format(currency_code))
        return self._currencies[currency_code]

    def get_open_orders(self):
        result = self._perform_request(lambda: self._handle.get_open_orders())
        output = []
        for item in result:
            base_code, market_code = self._split_sumbol(item['symbol'])
            amount = float(item['origQty'])
            output.append(TradeOrder(
                item["orderId"],
                self._currencies[base_code],
                self._currencies[market_code],
                dateparser.parse(str(item["time"])),
                None,
                amount,
                amount - float(item["executedQty"]),
                float(item["price"]),
                float(item["price"]),
                OrderType.limit_buy if item["side"] == "BUY" else OrderType.limit_sell
            ))
        return output

    def cancel_order(self, base_currency_code, market_currency_code, order_id):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.cancel_order(symbol=exchange_name,
                                                                         orderId=order_id))

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

    def get_deposit_history(self):
        result = self._perform_request(lambda: self._handle.get_deposit_history())
        output = []
        for i in result['depositList']:
            # TODO: somehow log this
            if i["asset"] not in self._currencies:
                continue
            output.append(
                Transfer(
                    self._currencies[i["asset"]],
                    float(i["amount"]),
                    i["txId"],
                    i["status"], # Status == 1 means success
                    0,
                    False,
                    dateparser.parse(str(i["insertTime"])),
                )
            )
        return output

    def buy(self, base_currency_code, market_currency_code, amount, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.order_limit_buy(symbol=exchange_name,
                                                                            quantity=amount,
                                                                            price=rate))
        return result['orderId']

    def sell(self, base_currency_code, market_currency_code, amount, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.order_limit_sell(symbol=exchange_name,
                                                                             quantity=amount,
                                                                             price=rate))
        return result['orderId']

    def get_deposit_address(self, currency_code):
        result = self._perform_request(lambda: self._handle.get_deposit_address(asset=currency_code))
        return CryptoAddress(
            currency_code,
            result['address'],
            result.get('addresTag', None)
        )

    def get_candles(self, base_currency_code, market_currency_code, interval, limit):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._perform_request(lambda:
            self._handle.get_klines(
                symbol=exchange_name,
                interval=BinanceWrapper.INTERVAL_MAP[interval],
                limit=limit
            )
        )
        output = []
        for i in result:
            output.append(Candle(
                float(i[3]), # Low
                float(i[2]), # High
                float(i[1]), # Open
                float(i[4]), # Close
                dateparser.parse(str(i[0]))
            ))
        return output

    def is_order_rate_valid(self, base_currency_code, market_currency_code, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        if exchange_name not in self._filters:
            return True
        order_filter = self._filters[exchange_name]
        if rate < order_filter.min_price:
            return OrderInvalidity(OrderInvalidity.Comparison.greater_eq, order_filter.min_price)
        elif rate > order_filter.max_price:
            return OrderInvalidity(OrderInvalidity.Comparison.lower_eq, order_filter.max_price)
        else:
            return True

    def is_order_amount_valid(self, base_currency_code, market_currency_code, amount):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        if exchange_name not in self._filters:
            return True
        order_filter = self._filters[exchange_name]
        if amount < order_filter.min_amount:
            return OrderInvalidity(OrderInvalidity.Comparison.greater_eq, order_filter.min_amount)
        elif amount > order_filter.max_amount:
            return OrderInvalidity(OrderInvalidity.Comparison.lower_eq, order_filter.max_amount)
        else:
            return True

    def is_order_notional_value_valid(self, base_currency_code, market_currency_code, rate, amount):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        if exchange_name not in self._filters:
            return True
        order_filter = self._filters[exchange_name]
        notional_value = rate * amount
        if notional_value < order_filter.min_notional:
            return OrderInvalidity(OrderInvalidity.Comparison.greater_eq, order_filter.min_notional)
        else:
            return True

    def _adjust_order_value(self, step, value):
        if step >= 1:
            return int(value / step) 
        else:
            decimals = utils.format_float(step).find('1') - 1
            meta_format = "{{0:0.{0}f}}".format(decimals)
            return float(meta_format.format(value))

    def adjust_order_rate(self, base_currency_code, market_currency_code, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        if exchange_name not in self._filters:
            return amount
        order_filter = self._filters[exchange_name]
        return self._adjust_order_value(order_filter.price_tick, rate)

    def adjust_order_amount(self, base_currency_code, market_currency_code, amount):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        if exchange_name not in self._filters:
            return amount
        order_filter = self._filters[exchange_name]
        return self._adjust_order_value(order_filter.amount_step, amount)
