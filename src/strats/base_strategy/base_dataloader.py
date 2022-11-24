import os
import gc
import ccxt
import time
import pandas as pd
import numpy as np

from glob import glob
from datetime import datetime
from pipe import select, where

from src.utils.alternate_bars import alt_tick_bars


class BaseDataLoader:
    def __init__(self, config):
        self.config = config
        self.symbol = config.symbol
        self.mode = config.mode
        self.formatted_symbol = self.symbol.replace("/", "-")
        self.ftx_symbol = config.ftx_symbol

        self.raw_trades_path = config.raw_trades_path
        self.alternate_bars_path = config.alternate_bars_path
        self.df_path = config.df_path

        self.feed_names = config.feed_names

        self.save_interval = 200000

        self.load_market()
        self.set_since_and_end()
        self.load_feed_dicts()


    def load_market(self):
        # load the market details
        while True:
            try:
                self.exchange = ccxt.binance({"enableRateLimit": True})
                self.markets = self.exchange.load_markets()
                self.market = self.exchange.market(self.symbol)
                break
            except:
                time.sleep(1)


    def load_feed_dicts(self):
        self.bars = dict()
        for feed_name in self.feed_names:
            self.bars[feed_name] = None

        self.trades_list = dict()
        for feed_name in self.feed_names:
            self.trades_list[feed_name] = []


    def load_bars(self, feed_name):
        # load the bars
        self.bars[feed_name] = pd.read_csv(f"{self.alternate_bars_path}/{self.formatted_symbol}_{feed_name}.csv")
    

    def set_since_and_end(self):
        now = datetime.utcnow()
        now = self.exchange.parse8601(now.strftime("%Y-%m-%dT%H:%M:%S"))
        self.start_time = now
        self.end = None
        self.one_hour = 3600 * 1000
        self.ten_days = 10 * 24 * 3600 * 1000
        self.backtest_start = self.config.backtest_start

        start, stop = self.get_saved_range()

        self.backfilling = False

        if self.mode == "live":
            self.delete_old_data(10)
            
            self.since = stop + 1
            self.end = now

            if self.since < now - self.ten_days:
                self.since = now - self.ten_days
                print(f"Since was less than 10 days ago. Setting to 10 days ago.")            

        else:
            self.bt_days = self.config.backtest_days * 24 * 3600 * 1000
            self.since = stop
            self.end = now

            if start > now - self.bt_days:
                self.since = now - self.bt_days
                self.end = stop  
                self.backfilling = True         


    def get_saved_range(self):
        """
        Get the range of timestamps that have been saved
        """
        paths = sorted(
            list(glob(f"{self.raw_trades_path}/*.csv.gz")
                | where(lambda x: self.formatted_symbol in x) 
            )
        )

        if len(paths) != 0:
            try:
                start = pd.read_csv(paths[0]).iloc[0]["timestamp"]
            except:
                start = 1609459200000
            try:
                stop = pd.read_csv(paths[-1]).iloc[-1]["timestamp"]
            except:
                stop = 1609459200000
        else:
            # start, stop is 2021-01-01 timestamp
            start, stop = 1609459200000, 1609459200000

        return start, stop


    def delete_old_data(self, days):
        for attempt in range(3):
            try:

                now = datetime.utcnow()
                now = self.exchange.parse8601(now.strftime("%Y-%m-%dT%H:%M:%S"))
                delete_days = now - (days * 24 * 3600 * 1000)

                paths = list(
                    glob(f"{self.raw_trades_path}/*.csv.gz")
                        | where(lambda x: self.formatted_symbol in x)
                )
               
                delete_paths = list(paths
                    | where(lambda x: int(x.split("_")[-1].split(".")[0]) < delete_days)
               )
                print(delete_days)
                #for p in delete_paths:
                #    os.remove(p)

            except:
                print("Error deleting old data")
                time.sleep(5)


    def get_trades(self, live=False):
     
        print(f"Getting trades for {self.symbol} from {self.since} to {self.end}")
        self.trades = []

        while self.since < self.end or live:
            try:
                trades = self.exchange.fetch_trades(self.symbol, int(self.since))
                self.trades.extend(trades)

                self.since += self.one_hour
                if len(self.trades) > self.save_interval:
                    self.dump_trades()
                    self.trades = []
            except Exception as e:
                print(e)
                time.sleep(1)

            if live:
                self.since = trades[-1]["timestamp"] + 1
                time.sleep(int(60 * 30))

        if len(self.trades) > 0:
            self.dump_trades()

        if self.backfilling:
            self.backfilling = False
            self.set_since_and_end()
            self.get_trades()

        print(f"Finished getting trades for {self.symbol}")


    def dump_trades(self):
        # get the latest saved timestamp
        _, cut_off = self.get_saved_range()

        # set column names
        columns = self.trades[0].keys()

        df = pd.DataFrame(self.trades, columns=columns)
        df = df.drop_duplicates(subset=["id"])
        df = df[df["timestamp"] > cut_off]
        last_timestamp = df["timestamp"].max()
        
        if len(df) == 0:
            return

        filename = (
            f"{self.raw_trades_path}/{self.formatted_symbol}_{last_timestamp}.csv.gz"
        )

        if len(self.trades) < self.save_interval and self.backfilling == False:
            
            filename = (
                f"{self.raw_trades_path}/{self.formatted_symbol}_partial_{last_timestamp}.csv.gz"
            )

        df.to_csv(filename, index=False)

        self.combine_partial_files()

        del df
        gc.collect()


    def combine_partial_files(self):
        paths = sorted(
            list(glob(f"{self.raw_trades_path}/*.csv.gz")
                | where(lambda x: self.formatted_symbol in x)
                | where(lambda x: "partial" in x)
            )
        )

        if len(paths) > 1:
            dfs = [pd.read_csv(p) for p in paths]
            df = pd.concat(dfs)
            df.sort_values("id", inplace=True)

            while True:
                if len(df) > self.save_interval:
                    mask = df.iloc[:self.save_interval]
                    df = df.iloc[~df.index.isin(mask.index)]

                    last_timestamp = mask.timestamp.max()
                    
                    filename = (
                        f"{self.raw_trades_path}/{self.formatted_symbol}_{last_timestamp}.csv.gz"
                    )

                    mask.to_csv(filename, index=False, compression="gzip")
                
                else:
                    
                    last_timestamp = df.timestamp.max()
                    
                    filename = (
                        f"{self.raw_trades_path}/{self.formatted_symbol}_partial_{last_timestamp}.csv.gz"
                    )

                    df.to_csv(filename, index=False, compression="gzip")
                    
                    break

            paths = sorted(
                list(glob(f"{self.raw_trades_path}/*.csv.gz")
                    | where(lambda x: self.formatted_symbol in x)
                    | where(lambda x: "partial" in x)
                    | where(lambda x: filename not in x)
                )
            )

            for p in paths:
                try:
                    os.remove(p)
                except Exception as e:
                    print(e)


    def set_active_feed(self, feed_name):

        self.percent_freq = float(feed_name.split("percent-")[-1].split("_")[0])
        self.tick_freq = float(feed_name.split("tick-")[-1].split("_")[0])
        self.time_freq = float(feed_name.split("time-")[-1].split("_")[0])
        self.volume_freq = float(feed_name.split("volume-")[-1].split("_")[0])

        self.freqs = np.array(
            [self.tick_freq, self.percent_freq, self.volume_freq, self.time_freq]
        )


    def fill_trades_list(self):
        self.since = int(min([df.timestamp.iloc[-1] for df in self.bars.values()]) * 1000)
        now = datetime.utcnow()
        self.end = self.exchange.parse8601(now.strftime("%Y-%m-%dT%H:%M:%S"))

        self.get_trades()
        
        for feed_name in self.feed_names:
            last_timestamp = int(self.bars[feed_name].iloc[-1].timestamp * 1000)
            self.trades_list[feed_name] = list(
                self.trades
                    |  where(lambda trade: int(trade["timestamp"]) > last_timestamp)
            )

        self.since = self.trades[-1]["timestamp"] + 1 


    def convert_to_bars(self, feed_name):
        """
        Args:
            feed_name (str): name of the feed to convert to bars

        Returns:
            pd.DataFrame: bars
        """
        self.set_active_feed(feed_name)
        
        bars = []
        cols = ["price", "amount", "cost", "side", "timestamp", "id"]

        count = 0

        file_path = (
            f"{self.alternate_bars_path}/{self.formatted_symbol}_{feed_name}.csv"
        )
        
        agg_data = None

        try:
            file = pd.read_csv(file_path)
            last_timestamp = file["timestamp"].max() * 1000
        except:
            file = None
            last_timestamp = 0

        files = sorted(
            list(glob(f"{self.raw_trades_path}/*.csv.gz"))
                | where(lambda x: self.formatted_symbol in x)
                | where(lambda x: int(x.split("_")[-1].split(".")[0]) > last_timestamp)
        )

        length_of_files = len(files)

        for filename in files:
            count += 1
            trades = pd.read_csv(
                filename,
                usecols=cols,
                compression="gzip",
            )
            if (length_of_files - count) % 10 == 0:
                print(
                    f"\r{length_of_files - count} remaining....",
                    end="",
                )

            trades = trades[trades["timestamp"] > last_timestamp]

            if len(trades) != 0:
                trades.sort_values(by="id", inplace=True)
                trades["id_diff"] = trades["id"].diff()
                
                if len(trades[trades.id_diff != 1]) > 1:
                    # check for missing trades
                    print(f"Error with {filename}")
                    print(trades[trades.id_diff != 1])
                    return
               
                trades["price"] = trades["price"].astype(np.float64)
                trades["amount"] = trades["amount"].astype(np.float64)
                trades["cost"] = trades["cost"].astype(np.float64)
                trades["side"] = trades["side"]
                trades["side"] = np.where(trades["side"] == "buy", 1.0, -1.0)
                trades["timestamp"] = trades["timestamp"].astype(np.int64) / 1000
                seconds = np.diff(trades["timestamp"])
                seconds = np.insert(seconds, 0, 1)
                trades["seconds"] = seconds
                trades["seconds"] = trades["seconds"].astype(np.float64)
                trades["seconds"] = np.where(trades.seconds > 1000, 1, trades.seconds)

                df_data = (
                    trades[["price", "amount", "cost", "side", "timestamp", "seconds"]]
                    .to_numpy()
                    .astype(np.float64)
                    .T
                )

                if agg_data is None:
                    first_vals = df_data[0]
                    agg_data = np.array(
                        [
                            first_vals[0],
                            first_vals[0],
                            first_vals[0],
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ]
                    )

                tmp_bars, agg_data = alt_tick_bars(
                    df_data,
                    agg_data,
                    self.freqs,
                )

                if tmp_bars is not None:
                    for bar in tmp_bars:
                        bars.append(bar)

                trades = None
                gc.collect()

        if len(bars) != 0:
            df = pd.DataFrame(
                bars,
                columns=[
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
                ],
            )
        else:
            df = pd.DataFrame([])

        if file is not None:
            df = pd.concat([file, df])

        df.drop_duplicates(subset=["timestamp"], inplace=True)
        df.to_csv(file_path, index=False)

        return df
