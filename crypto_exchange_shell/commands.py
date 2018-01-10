class BaseCommand:
    def usage(self):
        pass

    def execute(self, handle, params):
        pass

class MarketStateCommand(BaseCommand):
    def execute(self, handle, params):
        result = handle.get_market_state(params[0], params[1])
        print '''Ask:  {0}
Bid:  {1}
Last: {2}
'''.format(result.ask, result.bid, result.last)


class CommandManager:
    def __init__(self):
        self._commands = {
            'market_state' : MarketStateCommand()
        }

    def add_command(self, name, command):
        self._commands[name] = command

    def execute(self, handle, command, parameters):
        if command not in self._commands:
            raise Exception('Unknown command {0}'.format(command))
        self._commands[command].execute(handle, parameters)    
