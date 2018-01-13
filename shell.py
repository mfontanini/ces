#!/usr/bin/env python

import signal, traceback
from crypto_exchange_shell.bittrex_wrapper import BittrexWrapper
from crypto_exchange_shell.commands import CommandManager
from crypto_exchange_shell.shell_completer import ShellCompleter
from crypto_exchange_shell.core import Core
from crypto_exchange_shell.price_database import PriceDatabase
from crypto_exchange_shell.config_manager import ConfigManager
from crypto_exchange_shell.exceptions import *

price_db = PriceDatabase()
price_db.wait_for_data()
running = True

config_manager = ConfigManager()
try:
    config_manager.load('configs/bittrex.cfg')
except Exception as ex:
    print 'Error parsing config: {0}'.format(ex)

handle = BittrexWrapper(config_manager.api_key, config_manager.api_secret)
cmd_manager = CommandManager()
core = Core(handle, cmd_manager, price_db)
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
        cmd_manager.execute(core, tokens[0], tokens[1:])
    except ExchangeAPIException as ex:
        print 'Error calling API: {0}'.format(ex)
    except UnknownCommandException as ex:
        print 'Unknown command: {0}'.format(ex.command)
    except UnknownCurrencyException as ex:
        print 'Unknown currency: {0}'.format(ex.currency_code)
    except ParameterCountException as ex:
        print '"{0}" command expects {1} parameters'.format(ex.command, ex.expected)
    except CommandExecutionException as ex:
        print 'Error executing command: {0}'.format(ex)
    except Exception as ex:
        print 'Error: {0}'.format(ex)
        traceback.print_exc()
price_db.stop()
