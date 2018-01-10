from bittrex.bittrex import *
from models import *

class BittrexWrapper:
    def __init__(self, api_key, api_secret):
        self._handle = Bittrex(api_key, api_secret)
        self._markets = {}
        self._currencies = {}
        self._load_markets()

    def _add_currency(self, code, name):
        self._currencies[code] = Currency(code, name)

    def _make_market_name(self, base_currency_code, market_currency_code):
        return '{0}-{1}'.format(base_currency_code, market_currency_code)

    def _load_markets(self):
        result = self._handle.get_markets()
        for market in result['result']:
            base_currency = market['BaseCurrency']
            market_currency = market['MarketCurrency']
            if base_currency not in self._markets:
                self._markets[base_currency] = set()
            self._markets[base_currency].add(market_currency)
            self._add_currency(market_currency, market['MarketCurrencyLong'])
            self._add_currency(base_currency, market['BaseCurrencyLong'])

    def get_base_currencies(self):
        return [self._currencies[x] for x in self._markets.keys()]

    def get_markets(self, base_currency_code):
        if base_currency_code not in self._markets:
            raise Exception('Invalid base currency {0}'.format(base_currency_code))
        return [self._currencies[x] for x in self._markets[base_currency_code]]

    def get_market_state(self, base_currency_code, market_currency_code):
        market_name = self._make_market_name(base_currency_code, market_currency_code)
        result = self._handle.get_ticker(market_name)
        data = result['result']
        return MarketState(data['Ask'], data['Bid'], data['Last'])
