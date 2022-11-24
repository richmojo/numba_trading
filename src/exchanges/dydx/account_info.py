import time
import numpy as np
import ccxt


class AccountInfo:
    """Mixin to get exchange account info"""

    def get_account_balance(self):
        for attempt in range(5):
            try:
                account = self.exchange.private.get_account().data["account"]
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

        balance = float(account["equity"])
        return balance

    def get_account_info(self):
        for attempt in range(5):
            try:
                account = self.exchange.private.get_account().data["account"]
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

        return account

    def get_max_position(self):
        return (self.leverage * self.starting_balance) / self.price

    def get_open_orders(self, symbol=None):
        for attempt in range(2):
            try:
                orders = self.exchange.private.get_orders(
                    market=symbol, status="OPEN"
                ).data["orders"]
            except Exception as e:
                message = f"Could not fetch open orders with error: {e}"
                self.logger.send_trade_info(message)
            else:
                break
        else:
            self.logger.send_trade_info(f"Could not fetch open orders.")

        return orders

    def get_open_positions(self, symbol=None):
        for attempt in range(2):
            try:
                account = self.exchange.private.get_positions(
                    market=symbol, status="OPEN"
                )
                positions = account.data["positions"]
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

        if len(positions) == 0:
            return

        return positions

    def get_position(self, symbol=None):
        for attempt in range(2):
            try:
                account = self.exchange.private.get_positions(
                    market=symbol, status="OPEN"
                )
                positions = account.data["positions"]
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

        if len(positions) == 0:
            return 0

        position = 0
        for p in positions:
            position += float(p["size"])

        return position

    def get_pairs(self):
        for attempt in range(2):
            try:
                markets = self.exchange.public.get_markets().data["markets"]
            except Exception as e:
                message = f"Could not fetch markets with error: {e}"
                self.logger.send_trade_info(message)
            else:
                break
        else:
            self.logger.send_trade_info(f"Could not fetch markets.")
        pairs = []
        for market in markets.values():
            pairs.append(market["market"])
        return sorted(pairs)

    def get_price(self, symbol=None):
        """
        Get last price
        """
        for attempt in range(2):
            try:
                candles = self.exchange.public.get_candles(symbol, limit=1).data[
                    "candles"
                ][0]
                price = candles["close"]
            except Exception as e:
                time.sleep(0.5)
                print("Could not fetch last price with error: ", e)
            else:
                return price

    def market_specs(self):
        for attempt in range(2):
            try:
                markets = self.exchange.public.get_markets().data["markets"]
            except Exception as e:
                message = f"Could not fetch markets with error: {e}"
                self.logger.send_trade_info(message)
            else:
                break
        else:
            self.logger.send_trade_info(f"Could not fetch markets.")
        market = next((d for d in markets.values() if d["market"] == self.symbol), None)
        if market:
            self.min_order_size = float(market["minOrderSize"])
            self.order_increment = float(market["stepSize"])
            self.price_increment = float(market["tickSize"])
        else:
            self.logger.send_trade_info(
                f"Could not find dydx market for symbol {self.symbol}, exiting.",
            )
