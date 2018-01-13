from terminaltables import AsciiTable
from terminaltables.width_and_alignment import max_dimensions

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