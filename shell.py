#!/usr/bin/env python

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

import signal
import traceback
import argparse
from crypto_exchange_shell.exchanges.bittrex_wrapper import BittrexWrapper
from crypto_exchange_shell.exchanges.binance_wrapper import BinanceWrapper
from crypto_exchange_shell.commands import CommandManager
from crypto_exchange_shell.shell_completer import ShellCompleter
from crypto_exchange_shell.core import Core
from crypto_exchange_shell.price_database import PriceDatabase
from crypto_exchange_shell.config_manager import ConfigManager
from crypto_exchange_shell.output_manager import OutputManager
from crypto_exchange_shell.exceptions import *
from crypto_exchange_shell.storage import Storage
from crypto_exchange_shell.address_book import AddressBook
from crypto_exchange_shell.utils import ask_for_passphrase

parser = argparse.ArgumentParser(description='Crypto exchange shell')
parser.add_argument('-c', '--config', type=str, required=True,
                    help='path to configuration file')
parser.add_argument('-d', '--decrypt', action='store_true',
                    help='decrypt the configuration file')

try:
    args = parser.parse_args()
except Exception as ex:
    print 'Error parsing arguments: {0}'.format(ex)
    exit(1)

if args.decrypt:
    passphrase = ask_for_passphrase('Configuration file decryption passphrase: ')
    if passphrase is None:
        print 'Configuration file decryption passphrase is required'
        exit(1)

config_manager = ConfigManager()
try:
    if args.decrypt:
        config_manager.load_encrypted(args.config, passphrase)
    else:
        config_manager.load(args.config)
except Exception as ex:
    print 'Error parsing config: {0}'.format(ex)
    exit(1)

print 'Fetching data from exchange...'
try:
    if config_manager.exchange_name == 'bittrex':
        handle = BittrexWrapper(config_manager.api_key, config_manager.api_secret)
    elif config_manager.exchange_name == 'binance':
        handle = BinanceWrapper(config_manager.api_key, config_manager.api_secret)
    else:
        print 'Unkown exchange {0}'.format(config_manager.exchange_name)
        exit(1)
except Exception as ex:
    print 'Failed to create {0} handle: {1}'.format(config_manager.exchange_name, ex)
    exit(1)

try:
    storage = Storage(config_manager.database_path)
    address_book = AddressBook(storage, handle)
except Exception as ex:
    print 'Failed to initialize storage: {0}'.format(ex)
    exit(1)

price_db = PriceDatabase()
print 'Fetching latest crypto currency prices...'
price_db.wait_for_data()

running = True
output_manager = OutputManager()
cmd_manager = CommandManager()
core = Core(handle, cmd_manager, output_manager, address_book, price_db)
completer = ShellCompleter(core)
while running:
    try:
        line = raw_input('#> ')
    except KeyboardInterrupt:
        print ''
        continue
    except EOFError:
        running = False
        continue
    line = line.strip()
    if len(line) == 0:
        continue
    tokens = line.strip().split(' ')
    tokens = filter(lambda i: len(i) > 0, tokens)
    try:
        command = cmd_manager.get_command(tokens[0])
        if command.parse_args:
            params = tokens[1:]
        else:
            params = line.strip()[len(tokens[0]):].strip()
        cmd_manager.execute(core, tokens[0], params)
    except ExchangeAPIException as ex:
        output_manager.log_error(
            'API execution error',
            str(ex)
        )
    except UnknownCommandException as ex:
        output_manager.log_error(
            'Unknown command',
            'Command "{0}" doesn\'t exist',
            ex.command
        )
    except UnknownCurrencyException as ex:
        output_manager.log_error(
            'Unknown currency',
            'Currency "{0}" doesn\'t exist',
            ex.currency_code
        )
    except UnknownBaseCurrencyException as ex:
        output_manager.log_error(
            'Unknown base currency',
            '"{0}" is not a valid base currency',
            ex.currency_code
        )
    except UnknownMarketException as ex:
        output_manager.log_error(
            'Unknown market',
            'Market "{0}-{1}" doesn\'t exist',
            ex.base_currency_code,
            ex.market_currency_code
        )
    except ParameterCountException as ex:
        mappings = {
            ParameterCountException.Expectation.exact : 'exactly',
            ParameterCountException.Expectation.at_least : 'at least',
            ParameterCountException.Expectation.at_most : 'at most',
        }
        output_manager.log_error(
            'Parameter error',
            '"{0}" command expects {1} {2} parameter{3}',
            ex.command,
            mappings[ex.expectation],
            ex.expected,
            's' if ex.expected != 1 else ''
        )
    except CommandExecutionException as ex:
        output_manager.log_error(
            'Command execution error',
            str(ex)
        )
    except Exception as ex:
        print 'Error: {0}'.format(ex)
        traceback.print_exc()
price_db.stop()
