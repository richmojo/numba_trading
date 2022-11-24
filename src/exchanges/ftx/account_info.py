import time
import numpy as np
import ccxt


class AccountInfo:
    """Mixin to get exchange account info"""

    def market_specs(self):
        for attempt in range(2):
            try:
                markets = self.exchange.load_markets()
            except Exception as e:
                message = f"Could not fetch markets with error: {e}"
                self.logger.send_trade_info(message)
            else:
                break
        else:
            self.logger.send_trade_info(f"Could not fetch markets.")
            self.reset()
        market = next((d for d in markets.values() if d["id"] == self.symbol), None)
        if market:
            self.ccxt_symbol = market["symbol"]
            self.min_order_size = market["limits"]["amount"]["min"]
            self.order_increment = market["precision"]["amount"]
            self.price_increment = market["precision"]["price"]
        else:
            self.logger.send_trade_info(
                f"Could not find ccxt market for symbol {self.symbol}, exiting.",
            )
            self.reset()

    def get_position(self):
        for attempt in range(2):
            try:
                account = self.exchange.privateGetAccount()
                account = account["result"]
            except Exception as e:
                message = f"Could not fetch account stats with error: {e}"
                self.logger.send_trade_info(message)
                account = None
                continue
            else:
                break
        else:
            self.logger.send_trade_info("Could not fetch account stats.")

        if account == None:
            return

        positions = account["positions"]
        p = next(
            (position for position in positions if position["future"] == self.symbol),
            None,
        )
        if p:
            return float(p["netSize"])
        else:
            return 0.0

    def get_account_balance(self):
        for attempt in range(5):
            try:
                account = self.exchange.privateGetAccount()
            except Exception as e:
                message = f"Could not fetch account stats with error: {e}"
                account = None
                self.logger.send_trade_info(message)
                continue
            else:
                break
        if account == None:
            print("Could not fetch account stats.")
            return

        account = account["result"]
        return float(account["collateral"])

    def get_max_position(self):
        return (self.leverage * self.starting_balance) / self.price

    def get_last_price(self):
        """
        Get last price
        """
        for attempt in range(2):
            try:
                lookback = self.exchange.fetchOHLCV(self.symbol, "1m")
                price = lookback[-1][4]
            except Exception as e:
                time.sleep(0.5)
                print("Could not fetch last price with error: ", e)
            else:
                return price

