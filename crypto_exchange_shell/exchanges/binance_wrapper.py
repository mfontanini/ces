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

from binance.client import Client
from crypto_exchange_shell.models import *
from crypto_exchange_shell.exceptions import *
from crypto_exchange_shell.exchanges.base_exchange_wrapper import BaseExchangeWrapper

class BinanceWrapper(BaseExchangeWrapper):
    def __init__(self, api_key, api_secret):
        BaseExchangeWrapper.__init__(self)
        self._handle = Client(api_key, api_secret)
        self._load_markets()

    def _make_exchange_name(self, base_currency_code, market_currency_code):
        return '{0}{1}'.format(market_currency_code, base_currency_code)

    def _load_markets(self):
        result = self._handle.get_exchange_info()
        for symbol in result['symbols']:
            base_currency = symbol['quoteAsset']
            market_currency = symbol['baseAsset']
            self.add_currency(Currency(base_currency, base_currency, 0, 0))
            self.add_currency(Currency(market_currency, market_currency, 0, 0))
            self.add_market(base_currency, market_currency)

    def get_currency(self, currency_code):
        if currency_code not in self._currencies:
            raise InvalidArgumentException('Invalid currency {0}'.format(currency_code))
        return self._currencies[currency_code]

    def get_market_state(self, base_currency_code, market_currency_code):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._handle.get_all_tickers()
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
