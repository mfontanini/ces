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

from enum import Enum

class BaseException(Exception):
    pass

class ConfigException(BaseException):
    pass

class KeyMissingConfigException(ConfigException):
    def __init__(self, missing):
        ConfigException.__init__(self, '"{0}" key not found in config file'.format(missing))

class UnknownCurrencyException(BaseException):
    def __init__(self, currency_code):
        BaseException.__init__(self, 'Unknown currency {0}'.format(currency_code))
        self.currency_code = currency_code

class UnknownBaseCurrencyException(BaseException):
    def __init__(self, currency_code):
        BaseException.__init__(self, 'Unknown base currency {0}'.format(currency_code))
        self.currency_code = currency_code

class UnknownMarketException(BaseException):
    def __init__(self, base_currency_code, market_currency_code):
        BaseException.__init__(self, 'Unknown market {0}-{1}'.format(
            base_currency_code,
            market_currency_code
        ))
        self.base_currency_code = base_currency_code
        self.market_currency_code = market_currency_code

class ExchangeAPIException(BaseException):
    pass

class InvalidArgumentException(BaseException):
    pass

class CommandExecutionException(BaseException):
    pass

class UnknownCommandException(CommandExecutionException):
    def __init__(self, command):
        CommandExecutionException.__init__(self, 'Unknown command "{0}"'.format(command))
        self.command = command

class ParameterCountException(CommandExecutionException):
    Expectation = Enum('Expectation', 'exact at_least at_most')

    def __init__(self, command, expected, expectation=Expectation.exact):
        CommandExecutionException.__init__(self, 'Expected {0} parameters'.format(expected))
        self.command = command
        self.expected = expected
        self.expectation = expectation

class DuplicateParameterException(CommandExecutionException):
    def __init__(self, parameter):
        CommandExecutionException.__init__(self, 'Duplicate "{0}" parameter'.format(parameter))
        self.parameter = parameter

class InvalidParameterTypeException(CommandExecutionException):
    def __init__(self, parameter, type_name):
        CommandExecutionException.__init__(self, 'Failed to parse parameter {0}'.format(parameter))
        self.parameter = parameter
        self.type_name = type_name

class MissingParameterException(CommandExecutionException):
    def __init__(self, parameter):
        CommandExecutionException.__init__(self, 'Missing "{0}" parameter'.format(parameter))
        self.parameter = parameter

class MissingParametersException(CommandExecutionException):
    def __init__(self):
        CommandExecutionException.__init__(self, 'Missing parameters')

class ParameterParsingException(CommandExecutionException):
    def __init__(self, line):
        CommandExecutionException.__init__(self, 'Failed to parse parameter "{0}"'.format(line))
        self.line = line

class InvalidAmountException(BaseException):
    pass
