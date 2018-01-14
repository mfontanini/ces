from terminaltables import AsciiTable
from terminaltables.width_and_alignment import max_dimensions
import datetime
import dateparser
import sys
from dateutil.tz import tzutc, tzlocal

def make_price_string(base_currency_price, base_currency_code, currency_price):
    return '{0:.8f} {1} (${2})'.format(
        base_currency_price,
        base_currency_code,
        currency_price * base_currency_price
    )

def make_table_rows(title, table_data):
    table = AsciiTable(table_data, title)
    dimensions = max_dimensions(table.table_data, table.padding_left, table.padding_right)[:3]
    output = table.gen_table(*dimensions)
    return map(lambda i: ''.join(i), list(output))

def datetime_from_utc_time(str_time):
    return dateparser.parse(str_time).replace(tzinfo=tzutc()).astimezone(tz=tzlocal())

def show_operation_dialog():
    running = True
    while running:
        sys.stdout.write('Type "yes" or "no" to confirm or decline the operation: ')
        sys.stdout.flush()
        try:
            line = raw_input()
        except (KeyboardInterrupt, EOFError):
            return False
        if line == 'yes':
            return True
        elif line == 'no':
            return False
        else:
            print 'Invalid response'

