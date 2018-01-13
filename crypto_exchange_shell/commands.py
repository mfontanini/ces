class BaseCommand:
    def usage(self):
        pass

    def execute(self, core, params):
        pass

class MarketStateCommand(BaseCommand):
    def execute(self, core, params):
        result = core.exchange_handle.get_market_state(params[0], params[1])
        print '''Ask:  {0}
Bid:  {1}
Last: {2}
'''.format(result.ask, result.bid, result.last)

    def generate_parameters(self, core, current_parameters):
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


class CommandManager:
    def __init__(self):
        self._commands = {
            'state' : MarketStateCommand()
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
