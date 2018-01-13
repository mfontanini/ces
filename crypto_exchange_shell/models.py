class Currency:
    def __init__(self, code, name):
        self.code = code
        self.name = name

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

