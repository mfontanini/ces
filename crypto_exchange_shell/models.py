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

class Deposit:
    def __init__(self, currency, amount, address, transaction_id, confirmations):
        self.currency = currency
        self.amount = amount
        self.address = address
        self.transaction_id = transaction_id
        self.confirmations = confirmations
