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
from ces.exceptions import *

class OrderInvalidity:
    Comparison = Enum('Comparison', 'lower_eq greater_eq')

    def __init__(self, comparison, value):
        self.comparison = comparison
        self.value = value

class BaseExchangeWrapper:
    def __init__(self, exposes_confirmations=True):
        self._currencies = {}
        self._markets = {}
        self.exposes_confirmations = exposes_confirmations

    def add_currency(self, currency):
        self._currencies[currency.code] = currency

    def add_market(self, base_currency_code, market_currency_code):
        if base_currency_code not in self._markets:
            self._markets[base_currency_code] = set()
        self._markets[base_currency_code].add(market_currency_code)

    def check_valid_currency(self, currency_code):
        if currency_code not in self._currencies:
            raise UnknownCurrencyException(currency_code)

    def get_base_currencies(self):
        return [self._currencies[x] for x in self._markets.keys()]

    def get_currencies(self):
        return self._currencies.values()

    def get_currency(self, currency_code):
        self.check_valid_currency(currency_code)
        return self._currencies[currency_code]

    def get_markets(self, base_currency_code):
        if base_currency_code not in self._markets:
            raise UnknownBaseCurrencyException(base_currency_code)
        return [self._currencies[x] for x in self._markets[base_currency_code]]

    def is_order_rate_valid(self, base_currency_code, market_currency_code, rate):
        return True

    def is_order_amount_valid(self, base_currency_code, market_currency_code, rate):
        return True

    def is_order_notional_value_valid(self, base_currency_code, market_currency_code, rate, amount):
        return True

    def minimum_withdraw_limit(self, currency_code):
        return None

    def adjust_order_rate(self, base_currency_code, market_currency_code, rate):
        return rate

    def adjust_order_amount(self, base_currency_code, market_currency_code, amount):
        return amount

    def order_history_needs_asset(self):
        return False
