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

import argparse
from crypto_exchange_shell.utils import encrypt, decrypt_file, ask_for_passphrase

parser = argparse.ArgumentParser(description='Encrypt/decrypt config file')
parser.add_argument('-p', '--path', type=str, required=True, help='path to encrypt/decrypt')
parser.add_argument('-e', '--encrypt', action='store_true', help='encrypt the given path')
parser.add_argument('-d', '--decrypt', action='store_true', help='decrypt the given path')

try:
    args = parser.parse_args()
except Exception as ex:
    print 'Error parsing arguments: {0}'.format(ex)
    exit(1)

if args.encrypt and args.decrypt:
    print 'Only either encrypt or decrypt are valid at once'
    exit(1)
if not args.encrypt and not args.decrypt:
    print 'Missing encrypt/decrypt option'
    exit(1)

if args.encrypt:
    passphrase = ask_for_passphrase('Passphrase to use: ')
    if passphrase is None:
        print 'Aborted'
        exit(1)
    passphrase2 = ask_for_passphrase('Repeat passphrase: ')
    if passphrase != passphrase2:
        print 'Passphrases are different'
        exit(1)
    try:
        data = open(args.path).read()
        print encrypt(data, passphrase)
    except Exception as ex:
        print 'Error during encryption: {0}'.format(ex)
else:
    passphrase = ask_for_passphrase('Passphrase used for encryption: ')
    try:
        print decrypt_file(args.path, passphrase)
    except Exception as ex:
        print 'Error during decryption: {0}'.format(ex)

