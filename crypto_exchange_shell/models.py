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

from enum import Enum

class Currency:
    def __init__(self, code, name, min_confirmations, withdraw_fee):
        self.code = code
        self.name = name
        self.min_confirmations = min_confirmations
        self.withdraw_fee = withdraw_fee

    def __repr__(self):
        return 'Currency({0})'.format(self.code)

class Market:
    def __init__(self, base_currency, market_currency):
        self.base_currency = base_currency
        self.market_currency = market_currency

class MarketState:
    def __init__(self, ask, bid, last):
        self.ask = ask
        self.bid = bid
        self.last = last

    def __repr__(self):
        return 'MarketState(a={0}, b={1}, l={2})'.format(self.ask, self.bid, self.last)

class Order:
    def __init__(self, rate, quantity):
        self.rate = rate
        self.quantity = quantity

class Orderbook:
    def __init__(self):
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)

class Wallet:
    def __init__(self, currency, balance, available, pending, address):
        self.currency = currency
        self.balance = balance
        self.available = available
        self.pending = pending
        self.address = address

class Transfer:
    def __init__(self, currency, amount, transaction_id, confirmations, cost, cancelled):
        self.currency = currency
        self.amount = amount
        self.transaction_id = transaction_id
        self.confirmations = confirmations
        self.cost = cost
        self.cancelled = cancelled

OrderType = Enum('OrderType', 'limit_sell limit_buy')

class TradeOrder:
    ORDER_TYPE_TO_STRING = {
        OrderType.limit_sell : 'limit sell',
        OrderType.limit_buy : 'limit buy',
    }

    def __init__(self, order_id, base_currency, market_currency, date_open, date_closed, amount,
                 remaining, limit, price_per_unit, order_type):
        self.order_id = order_id
        self.base_currency = base_currency
        self.market_currency = market_currency
        self.date_open = date_open
        self.date_closed = date_closed
        self.amount = amount
        self.remaining = remaining
        self.limit = limit
        self.price_per_unit = price_per_unit
        self.order_type = order_type
        self.order_type_string = TradeOrder.ORDER_TYPE_TO_STRING[order_type]
