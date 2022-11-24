import numpy as np
import pandas as pd

import time

from src.strats.base_strategy.base_dataloader import BaseDataLoader
from src.strats.simple_ma.config import Config


class DataLoader(BaseDataLoader):
    def __init__(self, config):
        super().__init__(config)

        self.config = config

    
    def add_indicators(self, feed_name):
        # add indicators here

        # fast and slow moving averages
        self.bars[feed_name][f"{feed_name}_ma"] = self.bars[feed_name]["close"].rolling(self.config.ma_window).mean()
        self.bars[feed_name].dropna(inplace=True)
    
    
    def save_data(self, feed_name, live=False):
        if not live:
            self.set_active_feed(feed_name)
            self.load_bars(feed_name)
        
        self.add_indicators(feed_name)
        self.bars[feed_name] = self.bars[feed_name].loc[self.bars[feed_name].timestamp >= self.backtest_start]
        self.bars[feed_name].to_csv(f"{self.config.df_path}/{self.formatted_symbol}_{feed_name}.csv")

    
    def start_live_feeds(self):
        # start live feeds here
        
        # load and start all the feeds
        self.load_feed_dicts()

        for feed_name in self.feed_names:
            self.set_active_feed(feed_name)
            self.load_bars(feed_name)
            self.add_indicators(feed_name)
        
        self.fill_trades_list()

        while True:            

            trades = self.exchange.fetch_trades(self.symbol, int(self.since))
            if trades is not None and len(trades) > 0:
                self.since = trades[-1]["timestamp"] + 1
                
                # check for each feed
                for feed_name in self.feed_names:

                    # switch variables to correct feed
                    self.set_active_feed(feed_name)
                    self.trades_list[feed_name].extend(trades)

                    if len(self.trades_list[feed_name]) > 0:
                        
                        # convert trades to a dataframe
                        df = pd.DataFrame(self.trades_list[feed_name])
                        df.sort_values("id", inplace=True)
                        df.drop_duplicates(subset=["id"], inplace=True)

                        trades["timestamp"] = trades["timestamp"].astype(np.int64) / 1000
                        seconds = np.diff(trades["timestamp"])
                        seconds = np.insert(seconds, 0, 1)
                        trades["seconds"] = seconds
                        trades["seconds"] = trades["seconds"].astype(np.float64)
                        trades["seconds"] = np.where(trades.seconds > 1000, 1, trades.seconds)

                        ticks = len(df)
                        spread = np.abs((df["price"].iloc[-1] / df["price"].iloc[0]) - 1)
                        volume = df["amount"].sum()
                        open_time = df["seconds"].sum()

                        if (
                            (self.tick_freq == 0 or ticks >= self.tick_freq)
                            and (self.percent_freq == 0 or spread >= self.percent_freq)
                            and (self.volume_freq == 0 or volume >= self.volume_freq)
                            and (self.time_freq == 0 or open_time >= self.time_freq)
                            and ticks != 0
                        ):
                            #add bar to bars
                            
                            open_price = df["price"].iloc[0]
                            high_price = df["price"].max()
                            low_price = df["price"].min()
                            close_price = df["price"].iloc[-1]
                            buy_volume = df[df["side"] == "buy"]["amount"].sum()
                            sell_volume = df[df["side"] == "sell"]["amount"].sum()
                            buy_cost = df[df["side"] == "buy"]["cost"].sum()
                            sell_cost = df[df["side"] == "sell"]["cost"].sum()
                            buy_ticks = len(df[df["side"] == "buy"])
                            sell_ticks = len(df[df["side"] == "sell"])
                            open_time = df["seconds"].sum()
                            timestamp = df["timestamp"].iloc[-1]
                        
                            bar = [
                                open_price,
                                high_price,
                                low_price,
                                close_price,
                                buy_volume,
                                sell_volume,
                                buy_cost,
                                sell_cost,
                                buy_ticks,
                                sell_ticks,
                                open_time,
                                timestamp,
                            ]

                            columns = [
                                "open",
                                "high",
                                "low",
                                "close",
                                "buy_volume",
                                "sell_volume",
                                "buy_cost",
                                "sell_cost",
                                "buy_ticks",
                                "sell_ticks",
                                "seconds",
                                "timestamp",

                            ]

                            bar = pd.DataFrame([bar], columns=columns)
                            self.bars[feed_name] = self.bars[feed_name][columns]

                            self.bars[feed_name] = pd.concat([self.bars[feed_name], bar])
                            self.bars[feed_name] = self.bars[feed_name].iloc[-self.lookback:]
                            self.bars[feed_name].reset_index(drop=True, inplace=True)

                            self.save_data(feed_name, live=True)                       

                            self.trades_list[feed_name] = []

                time.sleep(1)
