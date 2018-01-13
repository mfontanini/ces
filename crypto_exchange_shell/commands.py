import utils
from terminaltables import AsciiTable

class BaseCommand:
    def usage(self):
        pass

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
                print base_currency
                return []
            return map(lambda i: i.code, core.exchange_handle.get_markets(base_currency))
        else:
            return []

class MarketStateCommand(BaseCommand):
    def execute(self, core, params):
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

    def _make_columns(self, order, currency_code, price):
        return [
            utils.make_price_string(order.rate, currency_code, price),
            str(order.quantity)
        ]

    def execute(self, core, params):
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
    def execute(self, core, params):
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
        table = AsciiTable(data, 'Wawllets')
        print table.table

    def generate_parameters(self, core, current_parameters):
        return []

class WalletCommand(BaseCommand):
    def execute(self, core, params):
        currency_code = params[0]
        price = core.price_db.get_currency_price(currency_code)
        wallet = core.exchange_handle.get_wallet(currency_code)
        make_price = lambda i: utils.make_price_string(i, currency_code, price)
        address = wallet.address if wallet.address else '<no address>'
        data = [
            ['Available balance', make_price(wallet.available)],
            ['Pending balance', make_price(wallet.pending)],
            ['Address', address]
        ]
        table = AsciiTable(data, '{0} wallet'.format(currency_code))
        table.inner_heading_row_border = False
        print table.table

    def generate_parameters(self, core, current_parameters):
        if len(current_parameters) == 0:
            return map(lambda i: i.code, core.exchange_handle.get_base_currencies())
        return []

class CommandManager:
    def __init__(self):
        self._commands = {
            'state' : MarketStateCommand(),
            'orderbook' : OrderbookCommand(),
            'wallets' : WalletsCommand(),
            'wallet' : WalletCommand(),
        }

    def add_command(self, name, command):
        self._commands[name] = command

    def execute(self, handle, command, parameters):
        if command not in self._commands:
            raise Exception('Unknown command {0}'.format(command))
        self._commands[command].execute(handle, parameters)    

    def get_command_names(self):
        return self._commands.keys()

    def get_command(self, name):
        if name not in self._commands:
            raise Exception('Command {0} does not exist'.format(name))
        return self._commands[name]
