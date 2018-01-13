class Core:
    def __init__(self, exchange_handle, cmd_manager, price_db):
        self.exchange_handle = exchange_handle
        self.cmd_manager = cmd_manager
        self.price_db = price_db
