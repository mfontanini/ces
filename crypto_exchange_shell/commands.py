import utils

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
        price = core.price_db.get_currency_price(params[0])
        result = core.exchange_handle.get_market_state(params[0], params[1])
        make_price = lambda i: utils.make_price_string(result.ask, params[0], price)
        print '''Ask:  {0}
Bid:  {1}
Last: {2}
'''.format(make_price(result.ask), make_price(result.bid), make_price(result.last))

    def generate_parameters(self, core, current_parameters):
        return self.generate_markets_parameters(core, current_parameters)

class OrderbookCommand(BaseCommand):
    MAX_LINES = 10
    BASE_ROW_FORMAT = '{{:<{0}}} | {{:<{1}}}'

    def _make_columns(self, price, currency_code, order):
        return [
            utils.make_price_string(order.rate, currency_code, price),
            str(order.quantity)
        ]

    def _compute_column_length(self, rows, column_index):
        max_length = 0
        for row in rows:
            max_length = max(max_length, len(row[column_index]))
        return max_length

    def execute(self, core, params):
        base_code = params[0]
        price = core.price_db.get_currency_price(base_code)
        (buy_orderbook, sell_orderbook) = core.exchange_handle.get_orderbook(
            base_code,
            params[1]
        )
        buy_rows = []
        sell_rows = []
        for i in range(OrderbookCommand.MAX_LINES):
            buy_rows.append(self._make_columns(price, base_code, buy_orderbook.orders[i]))
            sell_rows.append(self._make_columns(price, base_code, sell_orderbook.orders[i]))
        column_lengths = [
            self._compute_column_length(buy_rows, 0),
            self._compute_column_length(buy_rows, 1),
            self._compute_column_length(sell_rows, 0),
            self._compute_column_length(sell_rows, 1)
        ]
        buy_row_length = column_lengths[0] + column_lengths[1]
        sell_row_length = column_lengths[2] + column_lengths[3]
        buy_row_format = OrderbookCommand.BASE_ROW_FORMAT.format(
            column_lengths[0],
            column_lengths[1],
        )
        sell_row_format = OrderbookCommand.BASE_ROW_FORMAT.format(
            column_lengths[2],
            column_lengths[3],
        )
        border_line = '| {0} |'.format('-' * (buy_row_length + sell_row_length + 9))
        print border_line
        print '| {0} * {1} |'.format('Bids'.center(buy_row_length+3), 'Asks'.center(sell_row_length+3))
        print border_line
        print '| {0} * {1} |'.format(
            buy_row_format.format(
                'Rate'.center(column_lengths[0]),
                'Quantity'.center(column_lengths[1])
            ),
            sell_row_format.format(
                'Rate'.center(column_lengths[2]),
                'Quantity'.center(column_lengths[3])
            )
        )
        print '| {0}|{1} * {2}|{3} |'.format(
            '-' * (column_lengths[0] + 1),
            '-' * (column_lengths[1] + 1),
            '-' * (column_lengths[2] + 1),
            '-' * (column_lengths[3] + 1),
        )
        for i in range(len(buy_rows)):
            print '| {0} * {1} |'.format(
                buy_row_format.format(*buy_rows[i]),
                sell_row_format.format(*sell_rows[i])
            )
        print border_line

    def generate_parameters(self, core, current_parameters):
        return self.generate_markets_parameters(core, current_parameters)

class CommandManager:
    def __init__(self):
        self._commands = {
            'state' : MarketStateCommand(),
            'orderbook' : OrderbookCommand()
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
