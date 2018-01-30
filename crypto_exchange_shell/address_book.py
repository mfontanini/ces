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

from models import CryptoAddress, AddressBookEntry
from exceptions import *

class AddressBook:
    def __init__(self, storage, exchange_handle):
        self._storage = storage
        self._exchange_handle = exchange_handle
        self._entries = {}
        self.load()

    def load(self):
        self._entries = {}
        for name, values in self._storage.load_address_book().items():
            try:
                self._entries[name] = CryptoAddress(
                    self._exchange_handle.get_currency(values['currency']),
                    values['address']
                )
            except UnknownCurrencyException as ex:
                print 'Found unknown currency {0} in address book'.format(values['currency'])

    def add_entry(self, name, currency_code, address):
        self._storage.add_address_book(name, currency_code, address)
        self._entries[name] = CryptoAddress(
            self._exchange_handle.get_currency(currency_code),
            address
        )

    def remove_entry(self, name):
        if name not in self._entries:
            return False
        self._storage.remove_address_book(name)
        del self._entries[name]
        return True

    def get_entries(self, currency_code=None):
        output = []
        for name, address in self._entries.items():
            if currency_code is None or address.currency.code == currency_code:
                output.append(AddressBookEntry(name, address))
        return output
