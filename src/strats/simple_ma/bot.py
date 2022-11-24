import time
from datetime import datetime
from glob import glob

import pandas as pd
from pipe import where



import src.strats.simple_ma._numba as nb
from src.exchanges.load_exchange import load_exchange
from src.strats.simple_ma._named_tuples import *
from src.strats.base_strategy.base_bot import BaseBot


class Bot(BaseBot):
    def __init__(self, config):
        self.start_time = time.time()
        self.config = config
        self.binance_symbol = config.binance_symbol

        self.feed_names = config.feed_names

        self.exchange = load_exchange(config)
        self.logger = config.logger

        self.df_path = config.df_path

        self.feed_files = self.get_feed_glob()

        if config.mode != "backtest":    
            self.ready()

        self.exchange_state = config.exchange_state
        self.state = config.state
        self.params = config.params

        self.mode = config.mode

        self.saved_data = []

        try:
            self.logger.save_params(self.params)
        except:
            pass


    def ready(self):
        """
        Used to trigger a new event
            - In this example we use a change in either feed to trigger a new event
            - I usually will have one feed that is the most important and will trigger the event
                - For example, if I am trading on the 1m timeframe, I will use the 1m feed to trigger the event
                - And maybe also have a higher timeframe (could be based on percent, ticks, volume etc.) feed that will give a macro view
                    - But this doesnt actually drive starting a new step
        """
        while True:
            try:
                if self.feed_files != self.get_feed_glob() and sorted(self.feed_names) == self.get_feeds():
                    self.feed_files = self.get_feed_glob()
                    break      
            except:
                pass

            time.sleep(1)

    
    def get_step_data(self):

        timestamp = 0
        ma_s = dict()        
        
        for feed_name in self.feed_names:
            df = self.load_feed_data(feed_name)
            if df.iloc[-1]["timestamp"] > timestamp:
                timestamp = df.iloc[-1]["timestamp"]
                price = df.iloc[-1]["close"]
            
            ma_s[feed_name] = df.iloc[-1][f"{feed_name}_ma"]

        row = [timestamp,  price, ma_s["0_tick-500_volume-0_time-10"], ma_s["0.01_tick-0_volume-0_time-10"]]

        return row


    def get_backtest_data(self):
        dfs = []

        for feed_name in self.feed_names:
            df = self.load_feed_data(feed_name)
            dfs.append(df)

        df = pd.concat(dfs)
        df = df.sort_values("timestamp")
        df.fillna(method="ffill", inplace=True)
        
        df = df[["timestamp", "close", "0_tick-500_volume-0_time-10_ma", "0.01_tick-0_volume-0_time-10_ma"]]
        df.drop_duplicates(subset="timestamp", inplace=True)

        return df


    def step(self, row=None):
        if row is None:
            # load data
            row = self.get_step_data()

        # update the exchange state
        self.state = self.state._replace(price=row[1])
        self.exchange_state = self.exchange.update_account_values(self.state, self.exchange_state)
        
        # use numba to update the state
        # this is everything that doesnt have to do with api calls
        # not needed in this example because its so simple, but in a more complex algo it speeds things up
        self.state = nb.numba_step(row, self.state, self.exchange_state, self.params)

        # place the trade
        if self.state.trade != 0:
            self.exchange.place_trade(self.state)

        tick_ma = row[2]
        percent_ma = row[3]

        # log the end of the step
        try:
            logging_state = LoggingState(
                self.state.timestamp,
                self.state.price,
                tick_ma,
                percent_ma,
                self.exchange_state.max_position,
                self.exchange_state.position,
                self.state.trade,
                self.state.trade_type,
                self.exchange_state.account_value,
                self.exchange_state.wallet_usd,

            )
            self.params = self.logger.end_of_step(logging_state, self.params)
        except Exception as e:
            print(e)


