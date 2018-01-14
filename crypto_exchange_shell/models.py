from enum import Enum

class Currency:
    def __init__(self, code, name, min_confirmations):
        self.code = code
        self.name = name
        self.min_confirmations = min_confirmations

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

class Order:
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
        self.order_type_string = Order.ORDER_TYPE_TO_STRING[order_type]
