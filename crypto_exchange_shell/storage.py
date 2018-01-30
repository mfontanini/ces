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

from contextlib import closing
import sqlite3

class Storage:
    def __init__(self, db_path):
        self._handle = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        with closing(self._handle.cursor()) as cursor:
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS address_book (' \
                    'name VARCHAR(255) UNIQUE NOT NULL,' \
                    'currency VARCHAR(10) NOT NULL,' \
                    'address VARCHAR(255) NOT NULL' \
                ')'
            )

    def load_address_book(self):
        output = {}
        query = 'SELECT name, currency, address FROM address_book'
        with closing(self._handle.cursor()) as cursor:
            for row in cursor.execute(query):
                output[row[0]] = {
                    'currency' : row[1],
                    'address' : row[2],
                }
        return output

    def add_address_book(self, name, currency_code, address):
        query = 'INSERT INTO address_book (name, currency, address) '\
                'VALUES (?, ?, ?)'
        with closing(self._handle.cursor()) as cursor:
            cursor.execute(
                query,
                (name, currency_code, address)
            )
            self._handle.commit()

    def remove_address_book(self, name):
        with closing(self._handle.cursor()) as cursor:
            cursor.execute('DELETE FROM address_book WHERE name = ?', (name, ))
            self._handle.commit()
