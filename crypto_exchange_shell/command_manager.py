class CommandManager:
    def __init__(self):
        self._commands = {}

    def add_command(self, name, command):
        self._commands[name] = command

    def execute(self, command, parameters):
        if command not in self._commands:
            raise Exception('Unknown command {0}'.format(command))
        self._commands[command].execute(parameters)    
