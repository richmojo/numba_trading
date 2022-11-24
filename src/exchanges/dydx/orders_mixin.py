import numpy as np
import pandas as pd
import time
from dydx3.constants import TIME_IN_FORCE_GTT
import streamlit as st


class OrdersMixin:
    """Mixin for the exchange class that provides all order handling"""

    def round_price(self, n):
        recip = 1.0 / self.price_increment
        return round(n * recip) / recip


    def round_order(self, n):
        recip = 1.0 / self.order_increment
        return (round(n * recip) / recip)


    def market_order(self, symbol, trade):
        side = "BUY" if trade > 0 else "SELL"
        price = self.get_market_price(symbol, side)
        trade = abs(trade)

        order_params = {
            'expiration_epoch_seconds': int(time.time()) + 4 * 7 * 1440 * 60,
            'limit_fee': '0.015',
            'market': symbol,
            'order_type': 'LIMIT',
            'position_id': self.position_id,
            'post_only': False,
            'price': str(price),
            'side': side,
            'size': str(trade),
            'time_in_force': TIME_IN_FORCE_GTT,
        }

        response = self.exchange.private.create_order(**order_params)
        return response


    def limit_order(self, symbol, trade, price, reduce_only=False):
        side = "BUY" if trade > 0 else "SELL"
        trade = abs(trade)

        order_params = {
            'expiration_epoch_seconds': int(time.time()) + 4 * 7 * 1440 * 60,
            'limit_fee': '0.015',
            'market': symbol,
            'order_type': 'LIMIT',
            'position_id': self.position_id,
            'post_only': True,
            'price': str(price),
            'reduce_only': reduce_only,
            'side': side,
            'size': str(trade),
        }

        response = self.exchange.private.create_order(**order_params)
        return response

    

    def get_bbo(self, symbol, side):
        for attempt in range(2):
            try:
                response = self.exchange.public.get_orderbook(symbol)
                book = response.data
            except Exception as e:
                self.message.append(
                    f"Could not get bbo with error: {e}",
                )
            else:
                break
        else:
            return None
        
        bids = book['bids']
        asks = book['asks']

        if len(bids) == 0 or len(asks) == 0:
            return None

        bid = bids[0]['price']
        ask = asks[0]['price']

        if side == "BUY":
            return bid
        else:
            return ask

    def get_market_price(self, symbol, side):
        """
        Allow slippage to 5th place in the orderbook.
        """
        for attempt in range(2):
            try:
                response = self.exchange.public.get_orderbook(symbol)
                book = response.data
            except Exception as e:
                self.message.append(
                    f"Could not get bbo with error: {e}",
                )
            else:
                break
        else:
            return None
        
        bids = book['bids']
        asks = book['asks']

        if len(bids) == 0 or len(asks) == 0:
            return None

        bid = bids[5]['price']
        ask = asks[5]['price']

        if side == "BUY":
            return ask
        else:
            return bid

    def get_slippage(self, symbol, trade, price):
        for attempt in range(2):
            try:
                response = self.exchange.public.get_orderbook(symbol)
                book = response.data
            except Exception as e:
                self.message.append(
                    f"Could not get bbo with error: {e}",
                )
            else:
                break
        else:
            return None
        
        bids = book['bids']
        asks = book['asks']

        if len(bids) == 0 or len(asks) == 0:
            return None

        remaining_trade = trade
        if trade > 0:
            for bid in bids:
                entry_price = bid['price']
                remaining_trade -= bid['size']
                if remaining_trade <= 0:
                    break
        else:
            for ask in asks:
                entry_price = ask['price']
                remaining_trade += ask['size']
                if remaining_trade >= 0:
                    break

        slippage = (entry_price - price) / price
        return abs(slippage)

    def cancel_order(self, order_id):
        response = self.exchange.private.cancel_order(order_id)
        return response
        
    def chase_limit_order(self, symbol, trade, reduce_only=False):
        side = "BUY" if trade > 0 else "SELL"
        
        trade = self.round_order(trade)

        price = self.get_bbo(symbol, side)

        position = self.get_position(symbol)
        
        position_goal = self.round_order(trade + position)

        order_params = {
            'expiration_epoch_seconds': int(time.time()) + 4 * 7 * 1440 * 60,
            'limit_fee': '0.015',
            'market': symbol,
            'order_type': 'LIMIT',
            'position_id': self.position_id,
            'post_only': True,
            'price': str(price),
            'reduce_only': reduce_only,
            'side': side,
            'size': str(abs(trade)),
        }

        # place initial order
        response = self.exchange.private.create_order(**order_params)
        order_id = response.data['order']['id']
        time.sleep(1.0)

        # check if order was filled update trade if not
        while True:
            response = self.exchange.private.get_order_by_id(order_id)
            order = response.data['order']
            if order['status'] == 'FILLED' or self.get_position(symbol) == position_goal:
                self.exchange.private.cancel_all_orders(symbol)
                break
            else:
                trade = self.round_order(position_goal - self.get_position(symbol))
                
                if trade == 0:
                    self.exchange.private.cancel_all_orders(symbol)
                    break

                side = "BUY" if trade > 0 else "SELL"
                
                price = self.get_bbo(symbol, side)
                price = self.round_price(float(price))

                if self.round_price(float(order['price'])) != price:
                    response = self.exchange.private.create_order(
                        **dict(
                            order_params,
                            size=str(abs(trade)),
                            price=str(price),
                            cancel_id=order_id,
                        ),
                    )
                    
                    order_id = response.data['order']['id']
                    time.sleep(1.0)

        self.exchange.private.cancel_all_orders(symbol)
        
        # check to see if position is correct if not restart step
        if self.get_position(symbol) != position_goal:
            trade = position_goal - self.get_position(symbol)
            self.chase_limit_order(symbol, trade, reduce_only)

        return response


    def spam_client_id(self, symbol, trade, reduce_only=False):
        client_id = int(time.time() * 1000)

        side = "BUY" if trade > 0 else "SELL"
        price = self.get_bbo(symbol, side)

        pass

