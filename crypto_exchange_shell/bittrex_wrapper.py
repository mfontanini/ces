from bittrex.bittrex import *
from models import *
from exceptions import ExchangeAPIException
import utils

class BittrexWrapper:
    ORDER_TYPE_MAPPINGS = {
        'LIMIT_SELL' : OrderType.limit_sell,
        'LIMIT_BUY' : OrderType.limit_buy,
    }

    def __init__(self, api_key, api_secret):
        self._handle = Bittrex(api_key, api_secret)
        self._markets = {}
        self._currencies = {}
        self._load_markets()

    def _make_exchange_name(self, base_currency_code, market_currency_code):
        return '{0}-{1}'.format(base_currency_code, market_currency_code)

    def _load_currencies(self):
        result = self._handle.get_currencies()
        self._check_result(result)
        for data in result['result']:
            code = data['Currency']
            self._currencies[code] = Currency(
                code,
                data['CurrencyLong'],
                data['MinConfirmation']
            )

    def _load_markets(self):
        self._load_currencies()
        result = self._handle.get_markets()
        self._check_result(result)
        for market in result['result']:
            base_currency = market['BaseCurrency']
            market_currency = market['MarketCurrency']
            if base_currency not in self._markets:
                self._markets[base_currency] = set()
            self._markets[base_currency].add(market_currency)

    def _check_result(self, result):
        if not result['success']:
            raise ExchangeAPIException(result['message'])

    def get_base_currencies(self):
        return [self._currencies[x] for x in self._markets.keys()]

    def get_markets(self, base_currency_code):
        if base_currency_code not in self._markets:
            raise Exception('Invalid base currency {0}'.format(base_currency_code))
        return [self._currencies[x] for x in self._markets[base_currency_code]]

    def get_market_state(self, base_currency_code, market_currency_code):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._handle.get_ticker(exchange_name)
        self._check_result(result)
        data = result['result']
        return MarketState(data['Ask'], data['Bid'], data['Last'])

    def get_orderbook(self, base_currency_code, market_currency_code):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._handle.get_orderbook(exchange_name)
        self._check_result(result)
        data = result['result']
        buy_orderbook = Orderbook()
        sell_orderbook = Orderbook()
        for item in data['buy']:
            buy_orderbook.add_order(Order(item['Rate'], item['Quantity']))
        for item in data['sell']:
            sell_orderbook.add_order(Order(item['Rate'], item['Quantity']))
        return (buy_orderbook, sell_orderbook)

    def get_wallets(self):
        result = self._handle.get_balances()
        self._check_result(result)
        output = []
        for data in result['result']:
            currency = data['Currency']
            # Shouldn't happen. TODO: log this
            if currency not in self._currencies:
                continue
            balance = Wallet(
                self._currencies[currency],
                data['Balance'],
                data['Available'],
                data['Pending'],
                data['CryptoAddress']
            )
            output.append(balance)
        return output

    def get_wallet(self, currency_code):
        result = self._handle.get_balance(currency_code)
        self._check_result(result)
        data = result['result']
        return Wallet(
            self._currencies[currency_code],
            data['Balance'],
            data['Available'],
            data['Pending'],
            data['CryptoAddress']
        )

    def get_deposit_history(self):
        result = self._handle.get_deposit_history()
        self._check_result(result)
        output = []
        for data in result['result']:
            # TODO: log this
            if data['Currency'] not in self._currencies:
                continue
            try:
                deposit = Transfer(
                    self._currencies[data['Currency']],
                    data['Amount'],
                    data['TxId'],
                    data.get('Confirmations', 0),
                    0, # Cost,
                    False, # Cancelled
                )
                output.append(deposit)
            except Exception as ex:
                print 'Failed to parse deposit for currency "{0}": {1}'.format(
                    data['Currency'],
                    ex
                )
        return output

    def get_withdrawal_history(self):
        result = self._handle.get_withdrawal_history()
        self._check_result(result)
        output = []
        for data in result['result']:
            # TODO: log this
            if data['Currency'] not in self._currencies:
                continue
            try:
                deposit = Transfer(
                    self._currencies[data['Currency']],
                    data['Amount'],
                    data['TxId'],
                    data.get('Confirmations', 0),
                    data['TxCost'],
                    data['Canceled']
                )
                output.append(deposit)
            except Exception as ex:
                print 'Failed to parse withdrawal for currency "{0}": {1}'.format(
                    data['Currency'],
                    ex
                )
        return output

    def get_open_orders(self):
        result = self._handle.get_open_orders()
        self._check_result(result)
        output = []
        for data in result['result']:
            base_currency, market_currency = data['Exchange'].split('-')
            # TODO: log this
            if base_currency not in self._currencies or market_currency not in self._currencies:
                continue
            output.append(Order(
                data['OrderUuid'],
                self._currencies[base_currency],
                self._currencies[market_currency],
                utils.datetime_from_utc_time(data['Opened']),
                None, # Date closed
                data['Quantity'],
                data['QuantityRemaining'],
                data['Limit'],
                None, # Price per unit
                BittrexWrapper.ORDER_TYPE_MAPPINGS[data['OrderType']]
            ))
        return output

    def get_order_history(self):
        result = self._handle.get_order_history()
        self._check_result(result)
        output = []
        for data in result['result']:
            base_currency, market_currency = data['Exchange'].split('-')
            # TODO: log this
            if base_currency not in self._currencies or market_currency not in self._currencies:
                continue
            output.append(Order(
                data['OrderUuid'],
                self._currencies[base_currency],
                self._currencies[market_currency],
                None, # Date open
                utils.datetime_from_utc_time(data['TimeStamp']),
                data['Quantity'],
                data['QuantityRemaining'],
                data['Limit'],
                data['PricePerUnit'],
                BittrexWrapper.ORDER_TYPE_MAPPINGS[data['OrderType']]
            ))
        return output

    def cancel_order(self, order_id):
        result = self._handle.cancel(order_id)
        self._check_result(result)

    def buy(self, base_currency_code, market_currency_code, amount, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._handle.buy_limit(exchange_name, amount, rate)
        self._check_result(result)
        return result['result']['uuid']

    def sell(self, base_currency_code, market_currency_code, amount, rate):
        exchange_name = self._make_exchange_name(base_currency_code, market_currency_code)
        result = self._handle.sell_limit(exchange_name, amount, rate)
        self._check_result(result)
        return result['result']['uuid']
