def make_price_string(base_currency_price, base_currency_code, currency_price):
    return '{0:.8f} {1} (${2})'.format(
        base_currency_price,
        base_currency_code,
        currency_price * base_currency_price
    )
