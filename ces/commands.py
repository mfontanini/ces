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

import utils
import sys
import re
from terminaltables import AsciiTable
from exceptions import *
from models import CandleTicks, Candle
from simpleeval import simple_eval
from exchanges.base_exchange_wrapper import OrderInvalidity
from parameter_parser import *

try:
    import readline
except ImportError: #Window systems don't have GNU readline
    import pyreadline.windows_readline as readline
    readline.rl.mode.show_all_if_ambiguous = "on"

class BaseCommand:
    def __init__(self, name):
        self.name = name

    def usage(self, core):
        template = self.help_template(core)
        data = [
            ['Usage', template['usage'].format(self.name)],
            ['Description', template['long_description'].format(self.name)],
        ]
        if 'examples' in template:
            data.append(['Examples', template['examples'].format(self.name)])
        table = AsciiTable(data, self.name)
        table.inner_row_border = True
        return table.table

    def short_usage(self, core):
        return self.help_template(core)['short_description']

    def execute(self, core, params):
        pass

    def generate_markets_parameters(self, core, current_parameters):
        base_currency_codes = map(lambda i: i.code, core.exchange_handle.get_base_currencies())
        base_currency_codes = set(base_currency_codes)
        if len(current_parameters) == 0:
            return base_currency_codes
        elif len(current_parameters) == 1:
            base_currency = current_parameters[0]
            if base_currency not in base_currency_codes:
                return []
            return map(lambda i: i.code, core.exchange_handle.get_markets(base_currency))
        else:
            return []

    def format_date(self, datetime):
        return datetime.strftime("%Y-%m-%d %H:%M:%S")

    def split_args(self, raw_params):
        return filter(lambda i: len(i) > 0, raw_params.strip().split(' '))

    def parameter_parser(self, core):
        return self.PARAMETER_PARSER

    def help_template(self, core):
        return self.HELP_TEMPLATE

    def generate_parameter_options(self, current_parameters, options):
        # e.g. don't a valid option if the last parameter is already an option
        if current_parameters[-1] in options:
            return []
        options = filter(lambda i: i not in current_parameters, options)
        return options

    def _generate_options(self, core, parameter_name, existing_parameters):
        base_currency_codes = map(lambda i: i.code, core.exchange_handle.get_base_currencies())
        if parameter_name == 'base-currency':
            return base_currency_codes
        elif parameter_name == 'market-currency':
            base_currency = existing_parameters['base-currency']
            if base_currency not in base_currency_codes:
                return []
            return map(lambda i: i.code, core.exchange_handle.get_markets(base_currency))
        elif parameter_name == 'currency':
            return map(lambda i: i.code, core.exchange_handle.get_currencies())
        return self.generate_options(core, parameter_name, existing_parameters)

    def generate_options(self, core, parameter_name, existing_parameters):
        return []

    def generate_parameters(self, core, params):
        (options, existing_parameters) = self.parameter_parser(core).generate_next_parameters(params)
        visitor = utils.ParameterOptionVisitor()
        for option in options:
            option.apply_visitor(visitor)
        output = []
        output += map(lambda i: i.value, visitor.tokens)
        for option in visitor.parameters:
            output += self._generate_options(core, option.parameter.name, existing_parameters)
        return output

    def execute_command(self, core, raw_params):
        params = self.parameter_parser(core).parse(raw_params)
        self.execute(core, params)

class MarketsCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str, required=False)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} [base-currency]',
        'short_description' : 'list the available markets',
        'long_description' : '''List the available markets. When executed with no parameters,
this will print the base currencies that can be used. When
a base currency is provided, the markets for that currency
will be displayed.''',
        'examples' : '''Print the available markets for BTC (e.g. all BTC/X pairs):

{0} BTC'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'markets')

    def execute(self, core, params):
        if len(params) == 0:
            data = [['Currency', 'Name']]
            currencies = core.exchange_handle.get_base_currencies()
            currencies = sorted(currencies, key=lambda c: c.code)
            for c in currencies:
                data.append([c.code, c.name])
            table = AsciiTable(data)
        else:
            currencies = core.exchange_handle.get_markets(params['base-currency'])
            currencies = sorted(currencies, key=lambda m: m.code)
            data = [['Market', 'Currency name']]
            for c in currencies:
                data.append(['{0}/{1}'.format(params['base-currency'], c.code), c.name])
            table = AsciiTable(data)
        print table.table

class MarketStateCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str),
        PositionalParameter('market-currency', parameter_type=str),
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <market-currency>',
        'short_description' : 'get the market prices',
        'long_description' : '''Get the price at which the market <base-currency>/<market-currency>
is operating. ''',
        'examples' : '''Print the state of the BTC/XLM market:

{0} BTC XLM'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'market')

    def execute(self, core, params):
        base_currency_code = params['base-currency']
        market_currency_code = params['market-currency']
        price = core.coin_db.get_currency_price(base_currency_code)
        result = core.exchange_handle.get_market_state(base_currency_code, market_currency_code)
        make_price = lambda i: utils.make_price_string(
            i,
            base_currency_code,
            price,
            core.coin_db.fiat_currency
        )
        data = [
            ['Ask', make_price(result.ask)],
            ['Bid', make_price(result.bid)],
            ['Last', make_price(result.last)]
        ]
        table = AsciiTable(data, '{0}/{1} market'.format(base_currency_code, market_currency_code))
        table.inner_heading_row_border = False
        print table.table

class OrderbookCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str),
        PositionalParameter('market-currency', parameter_type=str),
    ])
    MAX_LINES = 10
    BASE_ROW_FORMAT = '{{:<{0}}} | {{:<{1}}}'
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <market-currency>',
        'short_description' : 'get a market\'s orderbook',
        'long_description' : 'Get the orderbook for the market <base-currency>/<market-currency>',
        'examples' : '''Print the orderbook of the BTC/XLM market:

{0} BTC XLM'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'orderbook')

    def _make_columns(self, order, base_currency_code, market_currency_code, price, fiat_currency):
        return [
            utils.make_price_string(order.rate, base_currency_code, price, fiat_currency),
            '{0:.2f} {1}'.format(order.quantity, market_currency_code)
        ]

    def execute(self, core, params):
        base_code = params['base-currency']
        market_code = params['market-currency']
        price = core.coin_db.get_currency_price(base_code)
        (buy_orderbook, sell_orderbook) = core.exchange_handle.get_orderbook(
            base_code,
            market_code
        )
        buy_rows = [['Rate', 'Quantity']]
        sell_rows = [['Rate', 'Quantity']]
        row_count = min(
            OrderbookCommand.MAX_LINES,
            len(buy_orderbook.orders),
            len(sell_orderbook.orders)
        )
        for i in range(row_count):
            buy_rows.append(self._make_columns(buy_orderbook.orders[i], base_code, market_code,
                                               price, core.coin_db.fiat_currency))
            sell_rows.append(self._make_columns(sell_orderbook.orders[i], base_code, market_code,
                                                price, core.coin_db.fiat_currency))

        buy_table_rows = utils.make_table_rows('Bids', buy_rows)
        sell_table_rows = utils.make_table_rows('Asks', sell_rows)
        for i in range(len(buy_table_rows)):
            print u'{0} {1}'.format(buy_table_rows[i], sell_table_rows[i])

class WalletsCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([])
    HELP_TEMPLATE = {
        'usage' : '{0}',
        'short_description' : 'get the wallets and their balances',
        'long_description' : 'Get all wallets. This will filter out the ones with no balance'
    }

    def __init__(self):
        BaseCommand.__init__(self, 'wallets')

    def execute(self, core, raw_params):
        wallets = core.exchange_handle.get_wallets()
        data = [['Currency', 'Total balance', 'Available balance', 'Pending/locked balance']]
        for wallet in sorted(wallets, reverse=True, key=lambda i: i.balance):
            # Stop once we reach 0 balances
            if wallet.balance == 0:
                break
            price = core.coin_db.get_currency_price(wallet.currency.code)
            data.append([
                '{0} ({1})'.format(wallet.currency.name, wallet.currency.code),
                utils.make_price_string(
                    wallet.balance,
                    wallet.currency.code,
                    price,
                    core.coin_db.fiat_currency
                ),
                utils.make_price_string(
                    wallet.available,
                    wallet.currency.code,
                    price,
                    core.coin_db.fiat_currency
                ),
                utils.make_price_string(
                    wallet.pending,
                    wallet.currency.code,
                    price,
                    core.coin_db.fiat_currency
                )
            ])
        # If we only have the labels
        if len(data) == 1:
            print 'No wallets currently have funds'
            return
        table = AsciiTable(data, 'wallets')
        print table.table

class WalletCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('currency', parameter_type=str),
    ])

    HELP_TEMPLATE = {
        'usage' : '{0} <currency>',
        'short_description' : 'get the balance for a specific wallet',
        'long_description' : 'Get the wallet information for <currency>',
        'examples' : '''Print the XLM wallet balance:

{0} XLM'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'wallet')

    def execute(self, core, params):
        currency = core.exchange_handle.get_currency(params['currency'])
        price = core.coin_db.get_currency_price(currency.code)
        wallet = core.exchange_handle.get_wallet(currency.code)
        make_price = lambda i: utils.make_price_string(
            i,
            currency.code,
            price,
            core.coin_db.fiat_currency
        )
        data = [
            ['Total balance', make_price(wallet.balance)],
            ['Available balance', make_price(wallet.available)],
            ['Pending/locked balance', make_price(wallet.pending)]
        ]
        table = AsciiTable(data, '{0} wallet'.format(currency.name))
        table.inner_heading_row_border = False
        print table.table

class DepositsCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([])
    CURRENCY_PARAMETER_PARSER = ParameterParser([
        PositionalParameter('currency', parameter_type=str)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0}',
        'short_description' : 'get the deposits made',
        'long_description' : 'Get the list of deposits made into wallets of this account'
    }

    def __init__(self):
        BaseCommand.__init__(self, 'deposits')

    def parameter_parser(self, core):
        if core.exchange_handle.transfers_needs_asset():
            return DepositsCommand.CURRENCY_PARAMETER_PARSER
        else:
            return DepositsCommand.PARAMETER_PARSER

    def execute(self, core, params):
        currency_code = params.get('currency', None)
        has_confirmations = core.exchange_handle.exposes_confirmations
        data = [
            ['Timestamp', 'Amount', 'Transaction id',
             'Confirmations' if has_confirmations else 'Status']
        ]
        for deposit in core.exchange_handle.get_deposit_history(currency_code):
            if has_confirmations:
                status = '{0}/{1}'.format(deposit.confirmations, deposit.currency.min_confirmations)
            else:
                status = 'Completed' if deposit.confirmations > 0 else 'Pending'
            data.append([
                self.format_date(deposit.timestamp),
                '{0} {1}'.format(deposit.amount, deposit.currency.code),
                deposit.transaction_id,
                status
            ])
        table = AsciiTable(data, 'Deposits')
        print table.table

class WithdrawalsCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([])
    CURRENCY_PARAMETER_PARSER = ParameterParser([
        PositionalParameter('currency', parameter_type=str)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0}',
        'short_description' : 'get the withdrawals made',
        'long_description' : 'Get the list of withdrawals made into wallets of this account'
    }

    def __init__(self):
        BaseCommand.__init__(self, 'withdrawals')

    def parameter_parser(self, core):
        if core.exchange_handle.transfers_needs_asset():
            return DepositsCommand.CURRENCY_PARAMETER_PARSER
        else:
            return DepositsCommand.PARAMETER_PARSER

    def execute(self, core, params):
        currency_code = params.get('currency', None)
        cost_index = 2
        withdrawals = core.exchange_handle.get_withdrawal_history(currency_code)
        data = [['Timestamp', 'Amount', 'Transaction id']]
        has_cost = any(map(lambda i: i.cost is not None, withdrawals))
        if has_cost:
            data[0].insert(2, 'Cost')
        for withdrawal in withdrawals:
            data.append([
                self.format_date(withdrawal.timestamp),
                '{0} {1}'.format(withdrawal.amount, withdrawal.currency.code),
                withdrawal.transaction_id
            ])
            if has_cost:
                if withdrawal.cancelled:
                    cost = '0 (cancelled)'
                else:
                    cost = '{0} {1}'.format(withdrawal.cost, withdrawal.currency.code)
                data[-1].insert(cost_index, cost)
        table = AsciiTable(data, 'Withdrawals')
        print table.table

class OrdersCommand(BaseCommand):
    DEFAULT_PARAMETER_PARSER = ParameterParser([
        ParameterChoice([
            ConstParameter('order-type', keyword='open'),
            ConstParameter('order-type', keyword='completed'),
        ]),
    ])
    ASSET_PARAMETER_PARSER = ParameterParser([
        ParameterChoice([
            ConstParameter('order-type', keyword='open'),
            ParameterGroup([
                PositionalParameter('base-currency', parameter_type=str),
                PositionalParameter('market-currency', parameter_type=str),
                ConstParameter('order-type', keyword='completed'),
            ])
        ])
    ])
    DEFAULT_HELP_TEMPLATE = {
        'usage' : '{0} <open|completed>',
        'short_description' : 'get the active and settled orders',
        'long_description' : '''Get the list of orders either completed or open depending
on the parameter used''',
        'examples' : '''Print the list of all open orders:

{0} open'''
    }
    ASSET_HELP_TEMPLATE = {
        'usage' : '{0} <open|<base-currency> <market-currency> <completed>>',
        'short_description' : 'get the active and settled orders',
        'long_description' : '''Get the list of orders either completed or open depending
on the parameter used. This exchange requires providing a base/market
currency pair for completed orders.''',
        'examples' : '''Print the list of all completed orders in the ETH/XLM market:

{0} ETH XLM completed'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'orders')

    def parameter_parser(self, core):
        return self.ASSET_PARAMETER_PARSER if core.exchange_handle.order_history_needs_asset() \
                                           else self.DEFAULT_PARAMETER_PARSER

    def help_template(self, core):
        return self.ASSET_HELP_TEMPLATE if core.exchange_handle.order_history_needs_asset() \
                                        else self.DEFAULT_HELP_TEMPLATE

    def execute(self, core, params):
        order_type = params['order-type']
        if order_type == 'open':
            data = [['Id', 'Exchange', 'Date', 'Type', 'Bid/Ask', 'Amount (filled/total)']]
            sort = lambda orders: sorted(orders, key=lambda i: i.date_open)
            for order in sort(core.exchange_handle.get_open_orders()):
                data.append([
                    order.order_id,
                    '{0}/{1}'.format(order.base_currency.code, order.market_currency.code),
                    self.format_date(order.date_open),
                    order.order_type_string,
                    '{0} {1}'.format(order.limit, order.base_currency.code),
                    '{0}/{1} {2}'.format(
                        order.amount - order.remaining,
                        order.amount,
                        order.market_currency.code
                    )
                ])
            title = 'Open orders'
        elif order_type == 'completed':
            data = [['Exchange', 'Date', 'Type', 'Price', 'Amount (filled/total)']]
            orders = core.exchange_handle.get_order_history(
                params.get('base-currency'),
                params.get('market-currency'),
            )
            sort = lambda orders: sorted(orders, key=lambda i: i.date_closed)
            for order in sort(orders):
                data.append([
                    '{0}/{1}'.format(order.base_currency.code, order.market_currency.code),
                    self.format_date(order.date_closed),
                    order.order_type_string,
                    '{0} {1}'.format(order.price_per_unit, order.base_currency.code),
                    '{0}/{1} {2}'.format(
                        order.amount - order.remaining,
                        order.amount,
                        order.market_currency.code
                    )
                ])
            title = 'Completed orders'
        else:
            raise CommandExecutionException('Invalid order type "{0}"'.format(order_type))
        # If we only have the titles
        if len(data) == 1:
            print 'No {0} orders found'.format(order_type)
        else:
            table = AsciiTable(data, title)
            print table.table

class CancelOrderCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str),
        PositionalParameter('market-currency', parameter_type=str),
        NamedParameter('order', parameter_type=str)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <market-currency> order <order-id>',
        'short_description' : 'cancel an order',
        'long_description' : '''Cancel the buy/sell order with id <order-id> which was posted
on the market <base-currency>/<market-currency>''',
        'examples' : '''Cancel an order posted in the ETH/BTC market:

{0} ETH BTC 8e84a510-fcd3-11e7-8be5-0ed5f89f718b'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'cancel')

    def execute(self, core, params):
        base_currency_code = params['base-currency']
        market_currency_code = params['market-currency']
        order_id = params['order']
        core.exchange_handle.cancel_order(base_currency_code, market_currency_code, order_id)
        print 'Successfully cancelled order {0}'.format(order_id)

    def generate_options(self, core, parameter_name, existing_parameters):
        if parameter_name == 'order':
            return map(lambda i: str(i.order_id), core.exchange_handle.get_open_orders())
        return []

class PlaceOrderBaseCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str),
        PositionalParameter('market-currency', parameter_type=str),
        NamedParameter('amount', parameter_type=str),
        SwallowInputParameter('rate'),
    ])

    def check_rate_and_amount(self, core, base_currency_code, market_currency_code, rate, amount):
        xchange = core.exchange_handle
        rate_check = xchange.is_order_rate_valid(
            base_currency_code,
            market_currency_code,
            rate
        )
        amount_check = xchange.is_order_amount_valid(
            base_currency_code,
            market_currency_code,
            amount
        )
        notional_check = xchange.is_order_notional_value_valid(
            base_currency_code,
            market_currency_code,
            rate,
            amount
        )
        mappings = {
            OrderInvalidity.Comparison.lower_eq : '<=',
            OrderInvalidity.Comparison.greater_eq : '>=',
        }
        if rate_check != True:
            raise CommandExecutionException('rate has to be {0} {1}'.format(
                mappings[rate_check.comparison],
                utils.format_float(rate_check.value)
            ))
        if amount_check != True:
            raise CommandExecutionException('amount has to be {0} {1}'.format(
                mappings[amount_check.comparison],
                utils.format_float(amount_check.value)
            ))
        if notional_check != True:
            fmt = 'notional value (amount * rate) has to be {0} {1} (order has {2})'
            raise CommandExecutionException(fmt.format(
                mappings[notional_check.comparison],
                utils.format_float(notional_check.value),
                utils.format_float(rate * amount),
            ))

class SellCommand(PlaceOrderBaseCommand):
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <market-currency> amount <amount|max> rate <rate>',
        'short_description' : 'place a sell order',
        'long_description' : '''Create a sell order for <amount> coins at rate <rate> in
the market <base-currency>/<market-currency>.

If the amount given is "max" then all of the coins in the wallet
for <market-currency> will be put in the order.

<rate> can be an expression. The "market" and "ask" constants can
be used which will contain the latest market and ask prices in this
market.''',
        'examples' : '''Sell 100 units of XLM at 10% more than what the latest ask
price is in the BTC market:

sell BTC XLM amount 100 rate 1.10 * ask

Another example, selling all of our units of ETH at 1 BTC each:

{0} BTC ETH amount max rate 1'''
    }

    def __init__(self):
        PlaceOrderBaseCommand.__init__(self, 'sell')

    def compute_amount(self, core, currency_code, amount):
        wallet = core.exchange_handle.get_wallet(currency_code)
        if amount == 'max':
            amount = wallet.available
        else:
            amount = float(amount)
        if amount > wallet.available:
            if wallet.available == 0:
                print '{0} wallet is empty'.format(currency_code)
            else:
                print 'Wallet only contains {0} {1}'.format(wallet.available, currency_code)
            return None
        return amount

    def execute(self, core, params):
        base_currency_code = params['base-currency']
        market_currency_code = params['market-currency']
        amount = params['amount']
        expression = params['rate']
        market_state = core.exchange_handle.get_market_state(
            base_currency_code,
            market_currency_code
        )
        try:
            names = {
                'market' : market_state.last,
                'ask' : market_state.ask
            }
            rate = simple_eval(expression, names=names)
        except Exception as ex:
            raise CommandExecutionException('Failed to evaluate expression: {0}'.format(ex))
        amount = self.compute_amount(core, market_currency_code, amount)
        if amount is None:
            return
        # Make sure the exchange accepts this rate/amount
        self.check_rate_and_amount(core, base_currency_code, market_currency_code, rate, amount)
        amount = core.exchange_handle.adjust_order_amount(
            base_currency_code,
            market_currency_code,
            amount
        )
        rate = core.exchange_handle.adjust_order_rate(
            base_currency_code,
            market_currency_code,
            rate
        )
        price = core.coin_db.get_currency_price(base_currency_code)
        data = [
            ['Exchange', 'Amount', 'Rate', 'Total price'],
        ]
        data.append([
            '{0}/{1}'.format(base_currency_code, market_currency_code),
            '{0} {1}'.format(amount, market_currency_code),
            utils.make_price_string(rate, base_currency_code, price, core.coin_db.fiat_currency),
            utils.make_price_string(
                rate * amount,
                base_currency_code,
                price,
                core.coin_db.fiat_currency
            )
        ])
        table = AsciiTable(data, 'Sell operation')
        print table.table
        if utils.show_operation_dialog():
            order_id = core.exchange_handle.sell(
                base_currency_code,
                market_currency_code,
                amount,
                rate
            )
            print 'Successfully posted order with id: {0}'.format(order_id)
        else:
            print 'Operation cancelled'

class BuyCommand(PlaceOrderBaseCommand):
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <market-currency> amount <amount|max> rate <rate>',
        'short_description' : 'place a buy order',
        'long_description' : '''Create a buy order for <amount> coins at rate <rate> in
the market <base-currency>/<market-currency>.

If the amount given is "max" then all of the coins in the wallet
for <base-currency> will be put in the order.

<rate> can be an expression. The "market" and "bid" constants can
be used which will contain the latest market and bid prices in
this market.''',
        'examples' : '''Buy 100 units of XLM at 90% of what the latest bid
price in the BTC market:

buy BTC XLM amount 100 rate 0.9 * bid

Another example, buying all of our units of ETH at 1 BTC each:

{0} BTC ETH amount max rate 1'''
    }

    def __init__(self):
        PlaceOrderBaseCommand.__init__(self, 'buy')

    def compute_amount(self, core, currency_code, amount, rate):
        wallet = core.exchange_handle.get_wallet(currency_code)
        if amount == 'max':
            amount = wallet.available / rate
        else:
            amount = float(amount)
            if amount > wallet.available:
                if wallet.available == 0:
                    raise CommandExecutionException('{0} wallet is empty'.format(currency_code))
                else:
                    raise CommandExecutionException('Wallet only contains {0} {1}'.format(
                        utils.format_float(wallet.available),
                        currency_code
                    ))
                return None
        return amount

    def execute(self, core, params):
        base_currency_code = params['base-currency']
        market_currency_code = params['market-currency']
        amount = params['amount']
        expression = params['rate']
        market_state = core.exchange_handle.get_market_state(
            base_currency_code,
            market_currency_code
        )
        try:
            names = {
                'market' : market_state.last,
                'bid' : market_state.bid
            }
            rate = simple_eval(expression, names=names)
        except Exception as ex:
            raise CommandExecutionException('Failed to evaluate expression: {0}'.format(ex))
        amount = self.compute_amount(core, base_currency_code, amount, rate)
        if amount is None:
            return
        # Make sure the exchange accepts this rate/amount
        self.check_rate_and_amount(core, base_currency_code, market_currency_code, rate, amount)
        amount = core.exchange_handle.adjust_order_amount(
            base_currency_code,
            market_currency_code,
            amount
        )
        rate = core.exchange_handle.adjust_order_rate(
            base_currency_code,
            market_currency_code,
            rate
        )
        price = core.coin_db.get_currency_price(base_currency_code)
        data = [
            ['Exchange', 'Amount', 'Rate', 'Total price'],
        ]
        data.append([
            '{0}/{1}'.format(base_currency_code, market_currency_code),
            '{0} {1}'.format(amount, market_currency_code),
            utils.make_price_string(rate, base_currency_code, price, core.coin_db.fiat_currency),
            utils.make_price_string(
                rate * amount,
                base_currency_code,
                price,
                core.coin_db.fiat_currency
            )
        ])
        table = AsciiTable(data, 'Buy operation')
        print table.table
        if utils.show_operation_dialog():
            order_id = core.exchange_handle.buy(
               base_currency_code,
               market_currency_code,
               amount,
               rate
            )
            print 'Successfully posted order with id: {0}'.format(order_id)
        else:
            print 'Operation cancelled'

class WithdrawCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('currency', parameter_type=str),
        NamedParameter('amount', parameter_type=str),
        ParameterChoice([
            NamedParameter('address', parameter_type=str),
            NamedParameter('address_book', parameter_type=str),
        ]),
        SwallowInputParameter('tag', required=False)
    ])

    HELP_TEMPLATE = {
        'usage' : '{0} <currency> amount <amount|max> address <address> [tag address-tag]',
        'short_description' : 'withdraw funds',
        'long_description' : '''Withdraw <amount> funds from the <currency> wallet into
a wallet with address <address>.

If <amount> is "max", then the entire contents of the wallet
are withdrawn.

For currencies that support a memo/payment id like XLM and
XMR, use the <address-tag> for this field.''',
        'examples' : '''Withdraw all of the XLM funds using a memo:

{0} XLM max C5JF5BT5VZIE this is my memo

Another example, 1 BTC:

{0} BTC 1 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2'''
    }

    ADDRESS_TAG_NAME = {
        'XLM' : 'Memo text',
        'XMR' : 'Payment id',
        'NXT' : 'Message',
        'XRP' : 'Tag',
    }

    def __init__(self):
        # For the memo/payment id we don't want parsing, we'll handle that ourselves
        BaseCommand.__init__(self, 'withdraw')

    def execute(self, core, params):
        currency_code = params['currency']
        amount = params['amount']
        if 'address' in params:
            address = params['address']
        else:
            entry = core.address_book.get_entry(params['address_book'])
            if entry is None:
                raise CommandExecutionException(
                    'Address book entry "{0}" does not exist'.format(params['address_book'])
                )
            address = entry.address
        address_tag = params.get('tag', None)
        currency = core.exchange_handle.get_currency(currency_code)
        wallet = core.exchange_handle.get_wallet(currency.code)
        if amount == 'max':
            amount = wallet.available
        else:
            amount = float(amount)
            if wallet.balance <= amount:
                raise CommandExecutionException(
                    'Wallet only contains {0} {1} (withdraw fee is {2})'.format(
                        wallet.available,
                        currency.code,
                        currency.withdraw_fee
                    )
                )
        minimum_withdraw = core.exchange_handle.minimum_withdraw_limit(currency_code)
        if minimum_withdraw and amount < minimum_withdraw:
            raise CommandExecutionException('Minimum withdraw is {0} {1}'.format(
                minimum_withdraw,
                currency_code
            ))
        data = [
            ['Currency', 'Amount', 'Tx fee', 'Address']
        ]
        price = core.coin_db.get_currency_price(currency.code)
        if currency.withdraw_fee is not None:
            fee_string = utils.make_price_string(
                currency.withdraw_fee,
                currency.code,
                price,
                core.coin_db.fiat_currency
            )
        else:
            fee_string = '<unknown>'
        data.append([
            currency.code,
            utils.make_price_string(
                amount - currency.withdraw_fee,
                currency.code,
                price,
                core.coin_db.fiat_currency
            ),
            fee_string,
            address
        ])
        if address_tag is not None:
            # Try to get our more specific namings if we have them
            data[0].append(WithdrawCommand.ADDRESS_TAG_NAME.get(currency.code, 'Address tag'))
            data[1].append(address_tag)
        table = AsciiTable(data, 'Withdrawal')
        print table.table
        if utils.show_operation_dialog():
            withdraw_id = core.exchange_handle.withdraw(
                currency.code,
                amount,
                address,
                address_tag
            )
            print 'Successfully posted withdraw order with id {0}'.format(withdraw_id)
        else:
            print 'Operation cancelled'

    def generate_options(self, core, parameter_name, existing_parameters):
        if parameter_name == 'address_book':
            currency_code = existing_parameters['currency']
            return map(lambda i: i.name, core.address_book.get_entries(currency_code))
        return []

class UsageCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('command', parameter_type=str)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <command>',
        'short_description' : 'print command\'s usage',
        'long_description' : '''Print the usage for <command>.

Note that elements inside <> are mandatory while the ones
inside [] are optional.''',
        'examples' : '''Print the usage for the withdraw command:

{0} withdraw'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'usage')

    def execute(self, core, params):
        print core.cmd_manager.get_command(params['command']).usage(core)

    def generate_options(self, core, parameter_name, existing_parameters):
        if parameter_name == 'command':
            return core.cmd_manager.get_command_names()
        return []

class HelpCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([])

    HELP_TEMPLATE = {
        'usage' : '{0}',
        'short_description' : 'print this help message',
        'long_description' : 'Print a help message'
    }

    def __init__(self):
        BaseCommand.__init__(self, 'help')

    def execute(self, core, raw_params):
        data = [['Command', 'Help']]
        for cmd in sorted(core.cmd_manager.get_command_names()):
            data.append([cmd, core.cmd_manager.get_command(cmd).short_usage(core)])
        table = AsciiTable(data, 'Commands')
        print table.table

class DepositAddressCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('currency', parameter_type=str)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <currency>',
        'short_description' : 'get the deposit address for a currency',
        'long_description' : 'Print the withdraw address for a specific currency.',
        'examples' : '''Get the deposit address for XLM:

{0} XLM'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'deposit_address')

    def execute(self, core, params):
        currency_code = params['currency']
        address = core.exchange_handle.get_deposit_address(currency_code)
        if address is None:
            raise CommandExecutionException(
                'Failed to fetch {0} address, try again later'.format(currency_code)
            )
        data = [['Address', address.address]]
        if address.address_tag:
            data.append([
                WithdrawCommand.ADDRESS_TAG_NAME[currency_code],
                address.address_tag
            ])
        table = AsciiTable(data, '{0} deposit address'.format(currency_code))
        table.inner_heading_row_border = False
        print table.table

class CandlesCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str),
        PositionalParameter('market-currency', parameter_type=str),
        ParameterChoice([
            ConstParameter('interval', keyword=i, required=False) for i in CandleTicks.__members__.keys()
        ])
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <market-currency> <interval>',
        'short_description' : 'fetch the price candles for a market',
        'long_description' : '''Fetch the price candles for the market <base-currency>/<market-currency>

The <interval> parameter must be one of one_minute, five_minutes,
thirty_minutes, one_hour and one_day.''',
        'examples' : '''Print the candles using a one hour interval for the
BTC/XLM market:

{0} BTC XLM one_hour'''
    }
    SAMPLE_COUNT = 50
    HEIGHT = 24

    def __init__(self):
        BaseCommand.__init__(self, 'candles')

    @classmethod
    def find_lowest_highest(cls, candles):
        lowest = None
        highest = None
        for i in candles:
            if lowest is None or i.lowest_price < lowest:
                lowest = i.lowest_price
            if highest is None or i.highest_price > highest:
                highest = i.highest_price
        return (lowest, highest)

    @classmethod
    def display_candles(cls, candles, matrix, lowest, highest, interval):
        y_values = map(
            lambda i: lowest + (i / float(CandlesCommand.HEIGHT)) * (highest - lowest),
            range(CandlesCommand.HEIGHT)
        )
        y_values.reverse()
        y_fmt_string = utils.make_appropriate_float_format_string(max(y_values))
        top_y_length = len(y_fmt_string.format(y_values[0]))

        for i in range(CandlesCommand.HEIGHT):
            y_label = y_fmt_string.format(y_values[i])
            # Append enough spaces to padd the length difference with the top label 
            sys.stdout.write('{0}{1} | '.format(y_label, (top_y_length - len(y_label)) * ' '))
            for column in matrix:
                sys.stdout.write(column[i] + " ")
            sys.stdout.write('\n')
        print u'\u2015' * (len(candles) * 2 + top_y_length + 2)
        label_length = 5
        x_labels = []
        for i in range(len(candles) - 1, 0, -4):
            x_labels.append(utils.make_candle_label(candles[i].timestamp, interval))
        x_labels.reverse()
        print ' ' * top_y_length + '   ' + '   '.join(x_labels)

    @classmethod
    def build_matrix(cls, candles, lowest, highest):
        matrix = []
        normalize = lambda v: (v - lowest) / (highest - lowest)
        for i in candles:
            open_value = normalize(i.open_price)
            close_value = normalize(i.close_price)
            low_value = normalize(i.lowest_price)
            high_value = normalize(i.highest_price)
            top = max(open_value, close_value)
            bottom = min(open_value, close_value)
            column = []
            total_written = 0
            for i in range(CandlesCommand.HEIGHT):
                value = i / float(CandlesCommand.HEIGHT)
                if value >= bottom and value <= top:
                    column.append(u'\u028C' if close_value > open_value else 'v')
                    total_written += 1
                elif value > low_value and value < high_value:
                    column.append(u'\u00A6')
                    total_written += 1
                else:
                    column.append(' ')
            if total_written == 0:
                column[int(high_value * (CandlesCommand.HEIGHT - 1))] = u'\u00A6'
            column.reverse()
            matrix.append(column)
        return matrix

    def execute(self, core, params):
        base_currency_code = params['base-currency']
        market_currency_code = params['market-currency']
        interval_string = params.get('interval', None)
        if interval_string is None:
            interval = CandleTicks.thirty_minutes
        else:
            interval = CandleTicks[interval_string]
        candles = core.exchange_handle.get_candles(
            base_currency_code,
            market_currency_code,
            interval,
            CandlesCommand.SAMPLE_COUNT
        )
        candles = candles[-CandlesCommand.SAMPLE_COUNT:]
        lowest, highest = self.find_lowest_highest(candles)
        matrix = self.build_matrix(candles, lowest, highest)
        self.display_candles(candles, matrix, lowest, highest, interval)

class CompoundCandlesCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('base-currency', parameter_type=str),
        PositionalParameter('source-currency', parameter_type=str),
        PositionalParameter('target-currency', parameter_type=str),
        ParameterChoice([
            ConstParameter('interval', keyword=i, required=False) for i in CandleTicks.__members__.keys()
        ])
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <base-currency> <source-currency> <target-currency> [interval]',
        'short_description' : 'compute the candles for two non tradeable currencies',
        'long_description' : '''Fetches the candles for <base-currency>/<source-currency> and
<base-currency>/<target-currency> and correlates their values. This
allows you to get candles for two currencies you can't directly trade.
For example, if there's a BTC/DOGE and a BTC/XLM market but not a
DOGE/XLM one, you can use this command to compute what the
historic price for DOGE/XLM would be.

The <interval> parameter must be one of one_minute, five_minutes,
thirty_minutes, one_hour and one_day.''',
        'examples' : '''Print the candles for a XRP/XLM market using ETH as the
intermediate currency to use:

{0} ETH XLM XRP'''
    }
    SAMPLE_COUNT = 50
    HEIGHT = 24

    def __init__(self):
        BaseCommand.__init__(self, 'compound_candles')

    def execute(self, core, params):
        base_currency_code = params['base-currency']
        source_currency_code = params['source-currency']
        target_currency_code = params['target-currency']
        interval_string = params.get('interval', None)
        if interval_string is None:
            interval = CandleTicks.thirty_minutes
        else:
            interval = CandleTicks[interval_string]
        candles_source = core.exchange_handle.get_candles(
            base_currency_code,
            source_currency_code,
            interval,
            CandlesCommand.SAMPLE_COUNT
        )
        candles_target = core.exchange_handle.get_candles(
            base_currency_code,
            target_currency_code,
            interval,
            CandlesCommand.SAMPLE_COUNT
        )
        samples = min(CandlesCommand.SAMPLE_COUNT, len(candles_source), len(candles_target))
        candles_source = candles_source[-samples:]
        candles_target = candles_target[-samples:]

        candles = []
        for i in range(len(candles_source)):
            source = candles_source[i]
            target = candles_target[i]
            candles.append(Candle(
                source.lowest_price / target.lowest_price,
                source.highest_price / target.highest_price,
                source.open_price / target.open_price,
                source.close_price / target.close_price,
                source.timestamp
            ))

        lowest, highest = CandlesCommand.find_lowest_highest(candles)
        matrix = CandlesCommand.build_matrix(candles, lowest, highest)
        CandlesCommand.display_candles(candles, matrix, lowest, highest, interval)

    def generate_options(self, core, parameter_name, existing_parameters):
        if parameter_name in ['source-currency', 'target-currency']:
            return map(
                lambda i: i.code,
                core.exchange_handle.get_markets(existing_parameters['base-currency'])
            )
        return []

class AddressBookCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        ParameterChoice([
            ParameterGroup([
                ConstParameter('action', keyword='list'),
                PositionalParameter('currency', parameter_type=str, required=False)
            ]),
            ParameterGroup([
                ConstParameter('action', keyword='add'),
                PositionalParameter('currency', parameter_type=str),
                NamedParameter('name', parameter_type=str),
                NamedParameter('address', parameter_type=str)
            ]),
            ParameterGroup([
                ConstParameter('action', keyword='remove'),
                NamedParameter('name', parameter_type=str),
            ]),
            ParameterGroup([
                ConstParameter('action', keyword='rename'),
                NamedParameter('name', parameter_type=str),
                NamedParameter('set', parameter_type=str),
            ])
        ])
    ])
    HELP_TEMPLATE = {
        'usage' : '{0}',
        'short_description' : 'manage address book',
        'long_description' : ''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'address_book')

    def execute(self, core, params):
        action = params['action']
        currency_code = params.get('currency', None)
        address = params.get('address', None)
        name = params.get('name', None)
        if action == 'list':
            entries = core.address_book.get_entries(currency_code)
            data = [
                ['Name', 'Currency', 'Address']
            ] 
            for entry in entries:
                data.append([
                    entry.name,
                    entry.address.currency.code,
                    entry.address.address
                ])
            if len(data) == 1:
                print 'No addresses in address book'
            else:
                table = AsciiTable(data, 'address book')
                print table.table
        elif action == 'add':
            core.address_book.add_entry(name, currency_code, address)
            print 'Added new {0} entry to address book'.format(currency_code)
        elif action == 'remove':
            if core.address_book.remove_entry(name):
                print 'Removed "{0}" entry from address book'.format(name)
            else:
                print '"{0}" is not in address book'.format(name)
        elif action == 'rename':
            core.address_book.rename_entry(name, params['set'])
            print 'Renamed "{0}" entry to "{1}"'.format(name, params['set'])

    def generate_options(self, core, parameter_name, existing_parameters):
        if parameter_name == 'name' and existing_parameters['action'] != 'add':
            return map(lambda i: i.name, core.address_book.get_entries())
        return []

class CoinInfoCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        PositionalParameter('currency', parameter_type=str)
    ])
    HELP_TEMPLATE = {
        'usage' : '{0} <currency>',
        'short_description' : 'print information about a currency',
        'long_description' : 'Prints the information about a currency',
        'examples' : '''Fetch the information about Ethereum:

{0} ETH'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'coin_info')

    def execute(self, core, params):
        metadata = core.coin_db.get_currency_metadata(params['currency'])
        fn = lambda value: '{0:,d}'.format(int(value)) if value >= 1000000 \
                                                       else utils.format_float(value)
        fmt_currency = lambda value: utils.format_fiat_currency(
            fn(value),
            core.coin_db.fiat_currency
        )
        data = [
            ['Name', metadata.name],
            ['Price', fmt_currency(metadata.price)],
            ['Rank', metadata.rank],
            ['24h volume', fmt_currency(metadata.volume_24h)],
            ['Market cap', fmt_currency(metadata.market_cap)],
            ['Available supply', '{0} {1}'.format(fn(metadata.available_supply), params['currency'])],
            ['Total supply', '{0} {1}'.format(fn(metadata.total_supply), params['currency'])],
        ]
        if metadata.max_supply is not None:
            data.append(['Max supply', '{0} {1}'.format(fn(metadata.max_supply), params['currency'])])
        data += [
            ['Change 1h', '{0}%'.format(fn(metadata.change_1h))],
            ['Change 24h', '{0}%'.format(fn(metadata.change_24h))],
            ['Change 7d', '{0}%'.format(fn(metadata.change_7d))],
        ]
        table = AsciiTable(data, '{0} information'.format(params['currency']))
        table.inner_heading_row_border = False
        print table.table

class CommandHistoryCommand(BaseCommand):
    PARAMETER_PARSER = ParameterParser([
        ParameterChoice([
            ConstParameter('action', keyword='clear'),
            ConstParameter('action', keyword='show')
        ])
    ])

    HELP_TEMPLATE = {
        'usage' : '{0} <clear|show>',
        'short_description' : 'manage command history',
        'long_description' : 'Manage the command history.',
        'examples' : '''Show the current command history:

history show

Clear the command history

history clear'''
    }

    def __init__(self):
        BaseCommand.__init__(self, 'history')

    def execute(self, core, params):
        count = readline.get_current_history_length()
        if params['action'] == 'clear':
            for i in range(count):
                readline.remove_history_item(0)
            print 'Removed {0} commands from history'.format(count)
        elif params['action'] == 'show':
            if count == 0:
                print 'No commands in history'
            else:
                for i in range(1, count + 1):
                    print readline.get_history_item(i)

class CommandManager:
    def __init__(self):
        self._commands = {}
        self.add_command(MarketStateCommand())
        self.add_command(MarketsCommand())
        self.add_command(OrderbookCommand())
        self.add_command(WalletsCommand())
        self.add_command(WalletCommand())
        self.add_command(DepositsCommand())
        self.add_command(WithdrawalsCommand())
        self.add_command(OrdersCommand())
        self.add_command(CancelOrderCommand())
        self.add_command(SellCommand())
        self.add_command(BuyCommand())
        self.add_command(WithdrawCommand())
        self.add_command(DepositAddressCommand())
        self.add_command(CandlesCommand())
        self.add_command(CompoundCandlesCommand())
        self.add_command(AddressBookCommand())
        self.add_command(CoinInfoCommand())
        self.add_command(CommandHistoryCommand())
        self.add_command(UsageCommand())
        self.add_command(HelpCommand())

    def add_command(self, command):
        self._commands[command.name] = command

    def execute_command(self, handle, command, parameters):
        if command not in self._commands:
            raise UnknownCommandException(command)
        self._commands[command].execute_command(handle, parameters)    

    def get_command_names(self):
        return self._commands.keys()

    def get_command(self, name):
        if name not in self._commands:
            raise UnknownCommandException(name)
        return self._commands[name]
