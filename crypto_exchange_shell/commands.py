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
from terminaltables import AsciiTable
from exceptions import *

class BaseCommand:
    def __init__(self, name, usage_template, short_usage_string, parse_args=True):
        self.name = name
        self.parse_args = parse_args
        self.usage_template = usage_template
        self.short_usage_string = short_usage_string

    def usage(self):
        output = self.usage_template.format(self.name)
        output = output.split('\n')
        output = [output[0]] + ['-' * len(output[0])] + output[1:]
        return '\n'.join(output)

    def short_usage(self):
        return self.short_usage_string

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

    def ensure_parameter_count(self, params, expected):
        if len(params) != expected:
            raise ParameterCountException(self.name, expected)

    def format_date(self, datetime):
        return datetime.strftime("%Y-%m-%d %H:%M:%S")

class MarketsCommand(BaseCommand):
    SHORT_USAGE_STRING = 'list the available markets'
    USAGE_TEMPLATE_STRING = '''{0} [base-currency]
List the available markets. When executed with no parameters,
this will print the base currencies that can be used. When
a base currency is provided, the markets for that currency
will be displayed.

For example, print the available markets for BTC (e.g. all BTC/X pairs):

markets BTC'''

    def __init__(self):
        BaseCommand.__init__(self, 'markets', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        if len(params) == 0:
            data = [['Currency']]
            codes = map(lambda i: i.code, core.exchange_handle.get_base_currencies())
            codes.sort()
            for i in codes:
                data.append([i])
            table = AsciiTable(data)
        elif len(params) == 1:
            markets = map(lambda i: i.code, core.exchange_handle.get_markets(params[0]))
            markets.sort()
            data = [['Market']]
            for i in markets:
                data.append(['{0}/{1}'.format(params[0], i)])
            table = AsciiTable(data)
        else:
            raise ParameterCountException(self.name, 0)
        print table.table

    def generate_parameter(sself, core, params):
        if len(params) == 0:
            return map(lambda i: i.code, core.exchange_handle.get_base_currencies())
        return []

class MarketStateCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the market prices'
    USAGE_TEMPLATE_STRING = '''{0} <base-currency> <market-currency>
Get the price at which the market <base-currency>/<market-currency>
is operating.

For example, print the state of the BTC/XLM market:

market BTC XLM'''

    def __init__(self):
        BaseCommand.__init__(self, 'market', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 2)
        base_currency_code = params[0]
        market_currency_code = params[1]
        price = core.price_db.get_currency_price(base_currency_code)
        result = core.exchange_handle.get_market_state(base_currency_code, market_currency_code)
        make_price = lambda i: utils.make_price_string(i, base_currency_code, price)
        data = [
            ['Ask', make_price(result.ask)],
            ['Bid', make_price(result.bid)],
            ['Last', make_price(result.last)]
        ]
        table = AsciiTable(data, '{0}/{1} market'.format(base_currency_code, market_currency_code))
        table.inner_heading_row_border = False
        print table.table

    def generate_parameters(self, core, current_parameters):
        return self.generate_markets_parameters(core, current_parameters)

class OrderbookCommand(BaseCommand):
    MAX_LINES = 10
    BASE_ROW_FORMAT = '{{:<{0}}} | {{:<{1}}}'
    SHORT_USAGE_STRING = 'get a market\'s orderbook'
    USAGE_TEMPLATE_STRING = '''{0} <base-currency> <market-currency>
Get the orderbook for the market <base-currency>/<market-currency>.

For example, print the orderbook of the BTC/XLM market:

market BTC XLM'''

    def __init__(self):
        BaseCommand.__init__(self, 'orderbook', self.USAGE_TEMPLATE_STRING,
                             self.SHORT_USAGE_STRING)

    def _make_columns(self, order, currency_code, price):
        return [
            utils.make_price_string(order.rate, currency_code, price),
            '{0:.2f}'.format(order.quantity)
        ]

    def execute(self, core, params):
        self.ensure_parameter_count(params, 2)
        base_code = params[0]
        price = core.price_db.get_currency_price(base_code)
        (buy_orderbook, sell_orderbook) = core.exchange_handle.get_orderbook(
            base_code,
            params[1]
        )
        buy_rows = [['Rate', 'Quantity']]
        sell_rows = [['Rate', 'Quantity']]
        for i in range(OrderbookCommand.MAX_LINES):
            buy_rows.append(self._make_columns(buy_orderbook.orders[i], base_code, price))
            sell_rows.append(self._make_columns(sell_orderbook.orders[i], base_code, price))

        buy_table_rows = utils.make_table_rows('Bids', buy_rows)
        sell_table_rows = utils.make_table_rows('Asks', sell_rows)
        for i in range(len(buy_table_rows)):
            print '{0} {1}'.format(buy_table_rows[i], sell_table_rows[i])

    def generate_parameters(self, core, current_parameters):
        return self.generate_markets_parameters(core, current_parameters)

class WalletsCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the wallets and their balances'
    USAGE_TEMPLATE_STRING = '''{0}
Get all wallets. This will filter out the ones with no balance.'''

    def __init__(self):
        BaseCommand.__init__(self, 'wallets', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 0)
        wallets = core.exchange_handle.get_wallets()
        data = [['Currency', 'Available balance', 'Pending']]
        for wallet in sorted(wallets, reverse=True, key=lambda i: i.balance):
            # Stop once we reach 0 balances
            if wallet.balance == 0:
                break
            price = core.price_db.get_currency_price(wallet.currency.code)
            data.append([
                wallet.currency.code,
                utils.make_price_string(wallet.available, wallet.currency.code, price),
                utils.make_price_string(wallet.pending, wallet.currency.code, price),
            ])
        # If we only have the labels
        if len(data) == 1:
            print 'No wallets currently have funds'
            return
        table = AsciiTable(data, 'wallets')
        print table.table

    def generate_parameters(self, core, current_parameters):
        return []

class WalletCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the balance for a specific wallet'
    USAGE_TEMPLATE_STRING = '''{0} <currency>
Get the wallet information for <currency>.

For example, print the XLM wallet balance:

market XLM'''

    def __init__(self):
        BaseCommand.__init__(self, 'wallet', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 1)
        currency_code = params[0]
        price = core.price_db.get_currency_price(currency_code)
        wallet = core.exchange_handle.get_wallet(currency_code)
        make_price = lambda i: utils.make_price_string(i, currency_code, price)
        data = [
            ['Available balance', make_price(wallet.available)],
            ['Pending balance', make_price(wallet.pending)]
        ]
        table = AsciiTable(data, '{0} wallet'.format(currency_code))
        table.inner_heading_row_border = False
        print table.table

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return map(lambda i: i.code, core.exchange_handle.get_base_currencies())
        return []

class DepositsCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the deposits made'
    USAGE_TEMPLATE_STRING = '''{0}
Get the list of deposits made into wallets of this account.'''

    def __init__(self):
        BaseCommand.__init__(self, 'deposits', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 0)
        data = [['Amount', 'Transaction id', 'Confirmations']]
        for deposit in core.exchange_handle.get_deposit_history():
            data.append([
                '{0} {1}'.format(deposit.amount, deposit.currency.code),
                deposit.transaction_id,
                '{0}/{1}'.format(deposit.confirmations, deposit.currency.min_confirmations)
            ])
        table = AsciiTable(data, 'Deposits')
        print table.table

    def generate_parameters(self, core, current_parameters):
        return []

class WithdrawalsCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the withdrawals made'
    USAGE_TEMPLATE_STRING = '''{0}
Get the list of withdrawals made into wallets of this account.'''

    def __init__(self):
        BaseCommand.__init__(self, 'withdrawals', self.USAGE_TEMPLATE_STRING,
                             self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 0)
        data = [['Amount', 'Transaction id', 'Cost']]
        for withdrawal in core.exchange_handle.get_withdrawal_history():
            if withdrawal.cancelled:
                cost = '0 (cancelled)'
            else:
                cost = '{0} {1}'.format(withdrawal.cost, withdrawal.currency.code)
            data.append([
                '{0} {1}'.format(withdrawal.amount, withdrawal.currency.code),
                withdrawal.transaction_id,
                cost
            ])
        table = AsciiTable(data, 'Withdrawals')
        print table.table

    def generate_parameters(self, core, current_parameters):
        return []

class OrdersCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the active and settled orders'
    USAGE_TEMPLATE_STRING = '''{0} <open|completed>
Get the list of orders either completed or open depending
on the parameter used.

For example, print the list of all open orders:

orders open'''

    def __init__(self):
        BaseCommand.__init__(self, 'orders', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 1)
        order_type = params[0]
        if order_type == 'open':
            data = [['Id', 'Exchange', 'Date', 'Type', 'Bid/Ask', 'Amount (filled/total)']]
            for order in core.exchange_handle.get_open_orders():
                data.append([
                    order.order_id,
                    '{0}/{1}'.format(order.base_currency.code, order.market_currency.code),
                    self.format_date(order.date_open),
                    order.order_type_string,
                    '{0} {1}'.format(order.limit, order.base_currency.code),
                    '{0}/{1}'.format(order.amount - order.remaining, order.amount)
                ])
            title = 'Open orders'
        elif order_type == 'completed':
            data = [['Exchange', 'Date', 'Type', 'Price', 'Amount (filled/total)']]
            for order in core.exchange_handle.get_order_history():
                data.append([
                    '{0}/{1}'.format(order.base_currency.code, order.market_currency.code),
                    self.format_date(order.date_closed),
                    order.order_type_string,
                    '{0} {1}'.format(order.price_per_unit, order.base_currency.code),
                    '{0}/{1}'.format(order.amount - order.remaining, order.amount)
                ])
            title = 'Completed orders'
        else:
            raise CommandExecutionException('Invalid order type "{0}"'.format(order_type))
        table = AsciiTable(data, title)
        print table.table

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return ['open', 'completed']
        return []

class CancelOrderCommand(BaseCommand):
    SHORT_USAGE_STRING = 'cancel an order'
    USAGE_TEMPLATE_STRING = '''{0} <order-id>
Cancel the buy/sell order with id <order-id>

For example:

cancel 8e84a510-fcd3-11e7-8be5-0ed5f89f718b'''

    def __init__(self):
        BaseCommand.__init__(self, 'cancel', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 1)
        order_id = params[0]
        core.exchange_handle.cancel_order(order_id)
        print 'Successfully cancelled order {0}'.format(order_id)

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return map(lambda i: i.order_id, core.exchange_handle.get_open_orders())
        return []

class SellCommand(BaseCommand):
    SHORT_USAGE_STRING = 'place a sell order'
    USAGE_TEMPLATE_STRING = '''{0} <base-currency> <market-currency> <amount|max> <rate>
Create a sell order for <amount> coins at rate <rate> in
the market <base-currency>/<market-currency>.

If the amount given is "max" then all of the coins in the wallet
for <market-currency> will be put in the order.

For example, sell 100 units of XLM at 0.1 BTC each:

sell BTC XLM 100 0.1

Another example, selling all of our units of ETH at 1 BTC each:

sell BTC ETH max 1'''

    def __init__(self):
        BaseCommand.__init__(self, 'sell', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 4)
        base_currency_code = params[0]
        market_currency_code = params[1]
        amount = params[2]
        rate = float(params[3])
        wallet = core.exchange_handle.get_wallet(market_currency_code)
        if amount == 'max':
            amount = wallet.available
        else:
            amount = int(amount)
        if amount > wallet.available:
            print 'Wallet only contains {0} {1}'.format(wallet.available, market_currency_code)
            return
        price = core.price_db.get_currency_price(base_currency_code)
        data = [
            ['Exchange', 'Amount', 'Rate', 'Total price'],
        ]
        data.append([
            '{0}/{1}'.format(base_currency_code, market_currency_code),
            amount,
            utils.make_price_string(rate, base_currency_code, price),
            utils.make_price_string(rate * amount, base_currency_code, price),
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

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) < 2:
            return self.generate_markets_parameters(core, current_parameters)
        return []

class BuyCommand(BaseCommand):
    SHORT_USAGE_STRING = 'place a buy order'
    USAGE_TEMPLATE_STRING = '''{0} <base-currency> <market-currency> <amount|max> <rate>
Create a buy order for <amount> coins at rate <rate> in
the market <base-currency>/<market-currency>.

If the amount given is "max" then all of the coins in the wallet
for <base-currency> will be put in the order.

For example, buy 100 units of XLM at 0.1 BTC each:

buy BTC XLM 100 0.1

Another example, buying all of our units of ETH at 1 BTC each:

buy BTC ETH max 1'''

    def __init__(self):
        BaseCommand.__init__(self, 'buy', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 4)
        base_currency_code = params[0]
        market_currency_code = params[1]
        amount = params[2]
        rate = float(params[3])
        wallet = core.exchange_handle.get_wallet(base_currency_code)
        if amount == 'max':
            amount = wallet.available
        else:
            amount = int(amount)
        if amount > wallet.available:
            print 'Wallet only contains {0} {1}'.format(wallet.available, base_currency_code)
            return
        price = core.price_db.get_currency_price(base_currency_code)
        data = [
            ['Exchange', 'Amount', 'Rate', 'Total price'],
        ]
        data.append([
            '{0}/{1}'.format(base_currency_code, market_currency_code),
            '{0} {1}'.format(amount, market_currency_code),
            utils.make_price_string(rate, base_currency_code, price),
            utils.make_price_string(rate * amount, base_currency_code, price)
        ])
        table = AsciiTable(data, 'Buy operation')
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

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) < 2:
            return self.generate_markets_parameters(core, current_parameters)
        return []

class WithdrawCommand(BaseCommand):
    SHORT_USAGE_STRING = 'withdraw funds'
    USAGE_TEMPLATE_STRING = '''{0} <currency> <amount|max> <address> [address-tag]
Withdraw <amount> funds from the <currency> wallet into
a wallet with address <address>.

If <amount> is "max", then the entire contents of the
wallet are withdrawn.

For currencies that support a memo/payment id like XLM and
XMR, use the <address-tag> for this field.

For example, withdraw all of the XLM funds using a memo:

withdraw XLM max C5JF5BT5VZIE this is my memo'''

    ADDRESS_TAG_NAME = {
        'XLM' : 'Memo text',
        'XMR' : 'Payment id',
        'NXT' : 'Message',
    }

    def __init__(self):
        # For the memo/payment id we don't want parsing, we'll handle that ourselves
        BaseCommand.__init__(self, 'withdraw', self.USAGE_TEMPLATE_STRING,
                             self.SHORT_USAGE_STRING, parse_args=False)

    def execute(self, core, raw_params):
        split_params = filter(lambda i: len(i) > 0, raw_params.strip().split(' '))
        if len(split_params) < 3:
            raise ParameterCountException(self.name, 3)
        currency = core.exchange_handle.get_currency(split_params[0])
        amount = split_params[1]
        wallet = core.exchange_handle.get_wallet(currency.code)
        if amount == 'max':
            amount = wallet.available - currency.withdraw_fee
        else:
            amount = float(amount)
            if wallet.balance <= amount:
                print 'Wallet only contains {0} {1} (withdraw fee is {2})'.format(
                    wallet.available,
                    currency.code,
                    currency.withdraw_fee
                )
                return
        address = split_params[2]
        address_tag = None
        # Find the address and use the rest of the string (if any) as the address tag.
        # The address tag is the payment id/memo depending on the currency being used
        index = raw_params.find(address) + len(address)
        rest = raw_params[index:].strip()
        if len(rest) > 0:
            address_tag = rest
        data = [
            ['Currency', 'Amount', 'Tx fee', 'Address']
        ]
        price = core.price_db.get_currency_price(currency.code)
        data.append([
            currency.code,
            utils.make_price_string(amount, currency.code, price),
            utils.make_price_string(currency.withdraw_fee, currency.code, price),
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

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return map(lambda i: i.code, core.exchange_handle.get_currencies())
        return []

class UsageCommand(BaseCommand):
    SHORT_USAGE_STRING = 'print command\'s usage'
    USAGE_TEMPLATE_STRING = '''{0} <command>
Print the usage for <command>.

Note that elements inside <> are mandatory while the ones
inside [] are optional

For example:

usage withdraw'''

    def __init__(self):
        BaseCommand.__init__(self, 'usage', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 1)
        print core.cmd_manager.get_command(params[0]).usage()

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return core.cmd_manager.get_command_names()
        return []

class HelpCommand(BaseCommand):
    SHORT_USAGE_STRING = 'print this help message'
    USAGE_TEMPLATE_STRING = '''{0}
Print a help message'''

    def __init__(self):
        BaseCommand.__init__(self, 'help', self.USAGE_TEMPLATE_STRING, self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 0)
        data = [['Command', 'Help']]
        for cmd in core.cmd_manager.get_command_names():
            data.append([cmd, core.cmd_manager.get_command(cmd).short_usage()])
        table = AsciiTable(data, 'Commands')
        print table.table

    def generate_parameters(self, core, current_parameters):
        return []

class DepositAddressCommand(BaseCommand):
    SHORT_USAGE_STRING = 'get the deposit address for a currency'
    USAGE_TEMPLATE_STRING = '''{0} <currency>
Print the withdraw address for a specific currency.

For example:

{0} XLM'''

    def __init__(self):
        BaseCommand.__init__(self, 'deposit_address', self.USAGE_TEMPLATE_STRING,
                             self.SHORT_USAGE_STRING)

    def execute(self, core, params):
        self.ensure_parameter_count(params, 1)
        currency_code = params[0]
        address = core.exchange_handle.get_deposit_address(currency_code)
        data = [['Address', address.address]]
        if address.address_tag:
            data.append([
                WithdrawCommand.ADDRESS_TAG_NAME[currency_code],
                address.address_tag
            ])
        table = AsciiTable(data, '{0} deposit address'.format(currency_code))
        table.inner_heading_row_border = False
        print table.table

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return map(lambda i: i.code, core.exchange_handle.get_base_currencies())
        return []

class CommandManager:
    def __init__(self):
        self._commands = {
            'market' : MarketStateCommand(),
            'markets' : MarketsCommand(),
            'orderbook' : OrderbookCommand(),
            'wallets' : WalletsCommand(),
            'wallet' : WalletCommand(),
            'deposits' : DepositsCommand(),
            'withdrawals' : WithdrawalsCommand(),
            'orders' : OrdersCommand(),
            'cancel' : CancelOrderCommand(),
            'sell' : SellCommand(),
            'buy' : BuyCommand(),
            'withdraw' : WithdrawCommand(),
            'deposit_address' : DepositAddressCommand(),
            'usage' : UsageCommand(),
            'help' : HelpCommand(),
        }

    def add_command(self, name, command):
        self._commands[name] = command

    def execute(self, handle, command, parameters):
        if command not in self._commands:
            raise UnknownCommandException(command)
        self._commands[command].execute(handle, parameters)    

    def get_command_names(self):
        return self._commands.keys()

    def get_command(self, name):
        if name not in self._commands:
            raise UnknownCommandException(name)
        return self._commands[name]
