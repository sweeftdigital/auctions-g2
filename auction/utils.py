def get_currency_symbol(currency_code):
    currency_symbols = {
        "GEL": "₾",  # Georgian Lari
        "USD": "$",  # US Dollar
        "EUR": "€",  # Euro
    }
    return currency_symbols.get(currency_code, "")
