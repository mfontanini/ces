class BaseException(Exception):
    pass

class ConfigException(BaseException):
    pass

class KeyMissingConfigException(ConfigException):
    def __init__(self, missing):
        ConfigException.__init__(self, '"{0}" key not found in config file')

class UnknownCurrencyException(BaseException):
    def __init__(self, currency_code):
        BaseException.__init__(self, 'Unknown currency {0}'.format(currency_code))
        self.currency_code = currency_code

class ExchangeAPIException(BaseException):
    pass

class CommandExecutionException(BaseException):
    pass

class UnknownCommandException(CommandExecutionException):
    def __init__(self, command):
        CommandExecutionException.__init__(self, 'Unknown command "{0}"'.format(command))
        self.command = command

class ParameterCountException(CommandExecutionException):
    def __init__(self, command, expected):
        CommandExecutionException.__init__(self, 'Expected {0} parameters'.format(expected))
        self.command = command
        self.expected = expected
