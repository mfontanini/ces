#!/usr/bin/env python

import signal
from crypto_exchange_shell.bittrex_wrapper import BittrexWrapper
from crypto_exchange_shell.commands import CommandManager
from crypto_exchange_shell.shell_completer import ShellCompleter
from crypto_exchange_shell.core import Core
from crypto_exchange_shell.price_database import PriceDatabase

handle = BittrexWrapper(None, None)
price_db = PriceDatabase()
price_db.wait_for_data()
running = True

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
    try:
        cmd_manager.execute(core, tokens[0], tokens[1:])
    except Exception as ex:
        print 'Error: {0}'.format(ex)
price_db.stop()
