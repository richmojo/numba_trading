import time
import numpy as np
import ccxt


class Manual:
    """
    Mixin for placing trades manually
    """

    def print_account_details(self):
        account = self.exchange.privateGetAccount()
        account = account["result"]
        print(f"Current balance: {account['balance']}")

        for position in account["positions"]:
            if float(position["netSize"]) != 0:
                print(
                    f"{position['symbol']} {position['side']} {position['netSize']} {position['avgEntryPrice']}"
                )

    def set_trade_goal(self, leverage=1.0):
        wallet = self.get_account_balance()
        return wallet * leverage

    def shotgun_order(
        self, high_price, low_price, symbol, leverage=1.0, trade_type="limit"
    ):
        """
        Place 20 limit orders equally distributed between the high and low price
        """
        trade_increment = (high_price - low_price) / 20
        trade_goal = self.set_trade_goal(leverage)
        trade = trade_goal / 20
        remainder = trade_goal
        price = low_price
        while remainder > 0:
            for attempt in range(2):
                try:
                    if trade_type == "take_profit":
                        order_id = self.take_profit_order(trade, price, symbol)
                    else:
                        order_id = self.limit_order(trade, price, symbol)
                except Exception as e:
                    message = f"Could not place order with error: {e}"
                    print(message)
                else:
                    break
            else:
                self.send_message("Could not place order.")
                return None
            price += trade_increment
            remainder -= trade
        return order_id
