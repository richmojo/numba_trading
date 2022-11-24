import time
import numpy as np


class Executions:
    def chase_limit_order(self, state):
        """
        Chase a limit order until it is filled.
        - Set the start time
        - Loop for 3 minutes or until filled
            - Update limit if possible
            - Post order loop
            - Check fill and send stop loop
        """
        start_time = time.time()
        t = time.time()

        trade = state.trade
        reduce_only = True if state.trade_type == "close" else False

        self.message = ["========================================="]
        self.message.append(f"Chasing limit order for {state.symbol} on {state.subaccount}, trade size: {trade}, trade_type: {state.trade_type} at price {state.price}")

        trade_goal = trade + self.position
        self.message.append(f"Trade goal: {trade_goal}")
        trade_sign = np.sign(trade)
        symbol = self.symbol

        while t - 180 <= start_time:
            t = time.time()
            self.position = self.get_position()
            trade_remaining = trade_goal - self.position
            trade_sign = np.sign(trade_remaining)

            if trade_remaining == 0:
                break

            elif abs(trade_remaining) > self.min_order_size:
                if trade_sign != 0 and trade_goal != self.position:
                    result = self.update_limit_price(
                            trade_sign, trade_remaining, symbol
                        )
                    time.sleep(0.5)
                    if result is None:
                        self.message.append("Could not update limit price adding new trade")
                        try:
                            self.cancel_open_orders(symbol)
                            self.position = self.get_position()
                            trade_remaining = trade_goal - self.position
                            
                            if trade_remaining == 0:
                                break

                            order_id = self.send_order_to_exchange(
                                trade_remaining, symbol, reduce_only
                            )

                            if order_id:
                                self.check_fill(
                                    order_id,
                                    symbol,
                                )
                            time.sleep(2.0)
                        except Exception as e:
                            self.message.append(f"Couldn't place order: {e}")
                    elif result == "error":
                        time.sleep(2.0)

                else:
                    self.message.append("No trade this step.")
                    break
            else:
                self.market_order(trade_remaining, symbol)
                break
        else:
            self.message.append(f"Could not place order, skipping this step.")

        status = self.position_check(symbol, trade_goal)

        if status == "not equal":
            self.message.append("Position not equal, trying to chase order.")
            trade = self.position - trade_goal
            self.chase_limit_order(trade, reduce_only)
        else:
            self.message.append("Position equal, moving on.")


        new_message = ""

        for m in self.message:
            new_message += f"{m} \n"

        if self.logger is not None:
            self.logger.send_trade_info(new_message)


        
