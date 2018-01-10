#!/usr/bin/env python

from crypto_exchange_shell.bittrex_wrapper import BittrexWrapper
from crypto_exchange_shell.commands import CommandManager
from crypto_exchange_shell.shell_completer import ShellCompleter

handle = BittrexWrapper(None, None)
#bases = wrapper.get_base_currencies()
#print wrapper.get_markets(bases[0])
#print wrapper.get_market_state('BTC', 'LTC')

completer = ShellCompleter()
command_manager = CommandManager()
while True:
    try:
        line = raw_input('#> ')
    except KeyboardInterrupt:
        exit(0)
    tokens = line.strip().split(' ')
    command_manager.execute(handle, tokens[0], tokens[1:])
