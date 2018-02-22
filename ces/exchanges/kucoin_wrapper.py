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

import dateparser
from kucoin.client import Client, KucoinAPIException
from ces.models import *
from ces.exceptions import *
from ces.exchanges.base_exchange_wrapper import *
import ces.utils as utils

class KucoinWrapper(BaseExchangeWrapper):
    INTERVAL_MAP = {
        CandleTicks.one_minute : Client.RESOLUTION_1MINUTE,
        CandleTicks.five_minutes : Client.RESOLUTION_5MINUTES,
        CandleTicks.thirty_minutes : Client.RESOLUTION_30MINUTES,
        CandleTicks.one_hour : Client.RESOLUTION_1HOUR,
        CandleTicks.one_day : Client.RESOLUTION_1DAY,
    }
    TIME_SINCE_MAP = {
        CandleTicks.one_minute : "1 hour ago",
        CandleTicks.five_minutes : "5 hours ago",
        CandleTicks.thirty_minutes : "26 hours ago",
        CandleTicks.one_hour : "52 hours ago",
        CandleTicks.one_day : "60 days ago",
    }
    ORDER_TYPE_MAPPINGS = {
        'BUY' : OrderType.limit_buy,
        'SELL' : OrderType.limit_sell,
    }

    def __init__(self, api_key, api_secret):
        BaseExchangeWrapper.__init__(self)
        self._handle = Client(api_key, api_secret)
        self._filters = {}
        self._load_markets()

    def _perform_request(self, request_lambda):
        try:
            return request_lambda()
        except KucoinAPIException as ex:
            raise ExchangeAPIException('Failed to perform request: {0}'.format(ex.message))

    def _load_currencies(self):
        result = self._perform_request(lambda: self._handle.get_coin_list())
        for coin in result:
            self.add_currency(
                Currency(
                    coin['coin'],
                    coin['name'],
                    coin['confirmationCount'],
                    coin['withdrawFeeRate'] # check if this is right
                )
            )

    def _load_markets(self):
        self._load_currencies()
        result = self._perform_request(lambda: self._handle.get_trading_symbols())
        for market in result:
            self.add_market(market['coinTypePair'], market['coinType'])

    def _make_symbol(self, base_currency_code, market_currency_code):
        return '{0}-{1}'.format(market_currency_code, base_currency_code)

    def _process_paged_request(self, make_request, callback):
        page = 1
        limit = 50
        data = self._perform_request(lambda: make_request(limit=limit, page=page))
        while len(data['datas']) > 0:
            for entry in data['datas']:
                callback(entry)
            page += 1
            data = make_request(limit=limit, page=page)

    def get_market_state(self, base_currency_code, market_currency_code):
        symbol = self._make_symbol(base_currency_code, market_currency_code)
        data = self._perform_request(lambda: self._handle.get_tick(symbol))
        return MarketState(data['sell'], data['buy'], data['lastDealPrice'])

    def get_orderbook(self, base_currency_code, market_currency_code):
        symbol = self._make_symbol(base_currency_code, market_currency_code)
        data = self._perform_request(lambda: self._handle.get_order_book(symbol))
        buy_orderbook = Orderbook()
        sell_orderbook = Orderbook()
        for item in data['BUY']:
            buy_orderbook.add_order(Order(item[0], item[1]))
        for item in data['SELL']:
            sell_orderbook.add_order(Order(item[0], item[1]))
        return (buy_orderbook, sell_orderbook)

    def get_candles(self, base_currency_code, market_currency_code, interval, limit):
        symbol = self._make_symbol(base_currency_code, market_currency_code)
        since = KucoinWrapper.TIME_SINCE_MAP[interval]
        kucoin_interval = KucoinWrapper.INTERVAL_MAP[interval]
        data = self._perform_request(
            lambda: self._handle.get_historical_klines_tv(symbol, kucoin_interval, since)
        )
        output = []
        for i in data:
            output.append(Candle(
                i[3], # Low
                i[2], # High
                i[1], # Open
                i[4], # Close
                dateparser.parse(str(i[0]))
            ))
        return output

    def get_wallets(self):
        output = []
        self._process_paged_request(
            self._handle.get_all_balances,
            lambda entry: output.append(Wallet(
                entry['coinType'],
                entry['balance'],
                entry['balance'] - entry['freezeBalance'],
                entry['freezeBalance']
            ))
        )
        return output

    def get_wallet(self, currency_code):
        self.check_valid_currency(currency_code)
        data = self._perform_request(lambda: self._handle.get_coin_balance(currency_code))
        return Wallet(
            self._currencies[currency_code],
            data['balance'],
            data['balance'] - data['freezeBalance'],
            data['freezeBalance']
        )

    def get_deposit_history(self, currency_code):
        request = lambda limit, page: self._handle.get_deposits(
            currency_code,
            limit=limit,
            page=page
        )
        output = []
        self._process_paged_request(
            request,
            lambda entry: output.append(Transfer(
                self._currencies[entry['coinType']],
                entry['amount'],
                entry['outerWalletTxid'], # is this right?
                1 if entry['status'] == 'FINISHED' else 0,
                0, # cost
                entry['status'] == 'CANCEL',
                dataparser.parse(str(entry['createdAt']))
            ))
        )
        return output

    def get_withdrawal_history(self, currency_code):
        request = lambda limit, page: self._handle.get_withdrawals(
            currency_code,
            limit=limit,
            page=page
        )
        output = []
        self._process_paged_request(
            request,
            lambda entry: output.append(Transfer(
                self._currencies[entry['coinType']],
                entry['amount'],
                entry['outerWalletTxid'], # is this right?
                0,
                entry['fee'],
                entry['status'] == 'CANCEL',
                dataparser.parse(str(entry['createdAt']))
            ))
        )
        return output

    def get_open_orders(self):
        raise ExchangeAPIException('Not implemented')

    def get_order_history(self):
        output = []
        self._process_paged_request(
            self._handle.get_dealt_orders,
            lambda entry: output.append(TradeOrder(
                data['orderOid'],
                self._currencies[base_currency],
                self._currencies[market_currency],
                None, # Date open
                dateparser.parse(str(data['createdAt'])),
                data['amount'],
                0, # Amount remaining
                data['dealPrice'],
                data['dealPrice'],
                KucoinWrapper.ORDER_TYPE_MAPPINGS[data['direction']]
            ))
        )
        return output

    def buy(self, base_currency_code, market_currency_code, amount, rate):
        symbol = self._make_symbol(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.create_buy_order(symbol, rate, amount))
        return result['orderOid']

    def sell(self, base_currency_code, market_currency_code, amount, rate):
        symbol = self._make_symbol(base_currency_code, market_currency_code)
        result = self._perform_request(lambda: self._handle.create_sell_order(symbol, rate, amount))
        return result['orderOid']

    def cancel_order(self, base_currency_code, market_currency_code, order_id):
        self._perform_request(lambda: self._handle.cancel_order(order_id, None))

    def withdraw(self, currency_code, amount, address, address_tag):
        if address_tag:
            raise ExchangeAPIException('Address tag not supported')
        self._perform_request(
            lambda: self._handle.create_withdrawal(currency_code, amount, address)
        )

    def get_deposit_address(self, currency_code):
        result = self._perform_request(lambda: self._handle.get_deposit_address(currency_code))
        return CryptoAddress(
            currency_code,
            result['address'],
            None
        )

    def transfers_needs_asset(self):
        return True
