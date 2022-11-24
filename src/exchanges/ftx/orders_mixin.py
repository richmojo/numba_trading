import numpy as np
import pandas as pd
import time
import ccxt


class OrdersMixin:
    """Mixin for the exchange class that provides all order handling"""

    def round_price(self, n):
        recip = 1.0 / self.price_increment
        return round(n * recip) / recip


    def round_order(self, n):
        recip = 1.0 / self.order_increment
        return round(n * recip) / recip


    def market_order(self, trade, symbol):
        order_side = "buy" if trade > 0 else "sell"
        response = self.exchange.create_order(
            symbol,
            "market",
            order_side,
            abs(trade),
        )
        return response


    def limit_order(self, trade, price, symbol, reduceOnly=False):
        order_side = "buy" if trade > 0 else "sell"
        response = self.exchange.create_order(
            symbol,
            "limit",
            order_side,
            abs(trade),
            price,
            params={"postOnly": True, "reduceOnly": reduceOnly},
        )
        return response


    def take_profit_order(self, trade, price, symbol):
        trade = self.round_order(trade)
        price = self.round_price(price)
        for attempt in range(2):
            try:
                response = self.limit_order(trade, price, symbol, reduceOnly=True)
            except Exception as e:
                self.message.append(
                    f"Could not send take profit with error: {e}",
                )
            else:
                break
        else:
            return None
        return response["id"]


    def stop_loss_order(self, trade, side, trigger_price, symbol):
        trade = self.round_order(trade)
        trigger_price = self.round_price(trigger_price)
        for attempt in range(2):
            try:
                response = self.exchange.privatePostConditionalOrders(
                    {
                        "market": symbol,
                        "side": side,
                        "triggerPrice": trigger_price,
                        "size": trade,
                        "type": "stop",
                        "reduceOnly": True,
                    }
                )
            except Exception as e:
                self.message.append(
                    f"Could not send stop with error: {e}",
                )
            else:
                break
        else:
            return None
        return response["result"]["id"]


    def fetch_bid_ask(self, trade_sign, symbol):
        for attempt in range(2):
            try:
                book = self.exchange.fetchOrderBook(symbol, 1)
            except Exception as e:
                self.message.append(
                    f"Could not fetch book with error: {e}",
                )
            else:
                break
        else:
            return None
        if trade_sign > 0:
            return book["bids"][0][0]
        else:
            return book["asks"][0][0]


    def post_order(self, trade, symbol, reduceOnly=False):
        self.get_position()

        if abs(trade) < self.min_order_size:
            return
        if abs(self.position) > abs(self.max_position) * 0.95 and np.sign(
            trade
        ) == np.sign(self.position):
            return
        
        price = self.fetch_bid_ask(np.sign(trade), symbol)
        if price is None:
            return None

        for attempt in range(2):
            try:
                response = self.limit_order(trade, price, symbol, reduceOnly)
                self.order_id = response["id"]
                return response["id"]
            
            except Exception as e:
                self.message.append(
                    f"Could not send order with error: {e}",
                )
        else:
            return None


    def check_order_posted(self, order_id, symbol):
        for attempt in range(2):
            try:
                response = self.exchange.fetchOrder(order_id, symbol)
            except Exception as e:
                self.message.append(
                    f"Could not check order with error: {e}",
                )
            else:
                break
        else:
            return None

        if response["status"] == "new":
            time.sleep(1.0)
            return self.check_order_posted(order_id)
        elif response["status"] == "open":
            return "posted"
        elif response["status"] == "closed" and response["filled"] != 0.0:
            return "posted"
        else:
            return "not posted"

 
    def send_order_to_exchange(self, trade, symbol, reduceOnly=False):
        self.message.append(
            f"Attempting to post order with size {trade}",
        )
        start_time = time.time()
        t = time.time()

        order_id = self.post_order(trade, symbol, reduceOnly)
        if order_id is None:
            print("Could not post order")
            return None
        time.sleep(2.0)

        posted = self.check_order_posted(order_id, symbol)
        if posted == "posted":
            print(f"Order posted... {order_id}")
            return order_id
        
        return None


    def check_order_filled(self, order_id, symbol):
        for attempt in range(2):
            try:
                response = self.exchange.fetchOrder(order_id, symbol)
            except Exception as e:
                self.message.append(f"Could not check order with error: {e}")
            else:
                break
        else:
            return None
        return response


    def amend_stop(self, stop_id, size, trigger_price):
        for attempt in range(2):
            try:
                response = self.exchange.request(
                    path=f"conditional_orders/{stop_id}/modify",
                    api="private",
                    method="POST",
                    params={
                        "triggerPrice": trigger_price,
                        "size": size,
                    },
                )
            except Exception as e:
                self.message.append(
                    f"Could not amend stop with error: {e}",
                )
            else:
                break
        else:
            return None
        return response["result"]["id"]


    def check_fill(self, order_id, symbol):
        """
        Check to see if order has been filled.
        """
        self.message.append(f"Watching for order fill and sending stop.")
        t = time.time()
        old_filled = 0.0
        new_filled = None
        amount = None
        for attempt in range(1):
            response = self.check_order_filled(order_id, symbol)
            if response:
                new_filled = response["filled"]
                remaining = response["remaining"]
                amount = response["amount"]
                # some or all filled
                if new_filled > old_filled:
                    self.message.append(
                        f"{new_filled} filled out of {amount} {symbol}.",
                    )
                # none filled, check again in 1 sec
                else:
                    time.sleep(0.5)
                    t = time.time()
                # completely filled, exit
                if remaining == 0.0:
                    self.message.append(
                        f"Order fully filled: {amount} {symbol}",
                    )
                    return
            else:
                time.sleep(1)
                t = time.time()
        else:
            self.message.append(
                f"Order did not fully fill: {new_filled} / {amount} {symbol}.",
            )
            return


    def update_limit_price(self, trade_sign, trade_remaining, symbol):
        """
        Update the limit price based on the
        symbol = order_data.symbol trade remaining.
        """
        if abs(trade_remaining) > self.min_order_size:
            response = self.exchange.request(
                "orders?market={market}",
                api="private",
                method="GET",
                params={"market": symbol},
            )
            result = response["result"]
            if len(result) == 0:
                return
            
            if len(result) > 1:
                print("More than one order found")
                return

            order = result[0]

            bid_ask = self.fetch_bid_ask(trade_sign, symbol)
            print(f"Updating limit price, moving price from {order['price']} to {bid_ask} to size {abs(trade_remaining)}")
            if bid_ask == order['price']:
                return
            try:
                return self.exchange.edit_order( order['id'], order['future'], order['type'], order['side'], amount=abs(trade_remaining), price=bid_ask, params={"type": order["type"]})
            except Exception as e:
                print(e)
                return "error"
        else:
            return None


    def cancel_open_orders(self, symbol):
        open_orders = self.number_of_open_orders(symbol)
        while open_orders > 0:
            try:
                response = self.exchange.request(
                    "orders?market={market}",
                    api="private",
                    method="GET",
                    params={"market": symbol},
                )
                response = pd.DataFrame(response["result"])
                print(f"Cancelling {len(response)} orders")
                try:
                    for i in range(len(response)):
                        order = response.iloc[i]
                        self.exchange.cancel_order(
                            order["id"], None, {"type": order["type"]}
                        )
                except:
                    self.message.append("Could not close open orders, none open")
            except Exception as e:
                self.message.append(f"Could not get open orders: {e}")

            time.sleep(1)
            open_orders = self.number_of_open_orders(symbol)            


    def number_of_open_orders(self, symbol):
        try:
            response = self.exchange.request(
                "orders?market={market}",
                api="private",
                method="GET",
                params={"market": symbol},
            )
            response = pd.DataFrame(response["result"])
            return len(response)
        except Exception as e:
            print(e)
            return 1


    def avg_fill_price(self, symbol, position_change):
        print(f"Getting average fill price for {symbol} with size {position_change}")
        trades = self.exchange.fetch_my_trades(symbol)

        if len(trades) == 0:
            return "No open positions"
        
        trades = pd.DataFrame(trades)
        trades = trades.sort_values(by="timestamp", ascending=False)

        if position_change > 0:
            trades = trades[trades["side"] == "buy"]
            if len(trades) == 0:
                return "No long trades"    
        else:
            trades = trades[trades["side"] == "sell"]
            if len(trades) == 0:
                return "No short trades"
        
        volume = 0
        cost = 0

        for i in trades.itertuples():
            if volume + i.amount >= abs(position_change):
                price = i.cost / i.amount
                trade_volume =  abs(position_change) - volume
                trade_cost = price * trade_volume
            else:
                trade_volume = i.amount
                trade_cost = i.cost
            
            volume += trade_volume
            cost += trade_cost

            if volume >= abs(position_change):
                return cost / volume


    def position_check(self, symbol, trade_goal):
        """
        Loop that checks to see if position is correct.
        """
        print("Checking position")
        self.cancel_open_orders(symbol)
        time.sleep(2.0)
        
        self.position = self.get_position()
        if self.position != trade_goal:
            return "not equal"
        else:
            return "equal"

