

class BaseExchange:
    def __init__(self):
        pass

    def place_trade(self, trade, position):
        raise AssertionError("Not implemented")

    def update_account_values(self):
        raise AssertionError("Not implemented")