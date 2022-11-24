import sys

sys.path.append("/home/richmojo/trading-projects/numba_trading")

import vectorbt as vbt
import numpy as np
import pandas as pd
import ray
from pipe import where
from glob import glob

from src.strats.simple_ma.dataloader import DataLoader
from src.strats.simple_ma.config import Config
from src.strats.simple_ma.ray_tasks import *

#====================================
# Get the data
#====================================

symbol = "SOL/USDT"
fresh_data = True
backtest_days = 100

config = Config(backtest_days=100, fresh_data=fresh_data, symbol=symbol)

if fresh_data:
    ray.get(prepare_backtest_gpu.remote([config]))


#====================================
# Convert the feeds into one df
#====================================

# Use this in your bot class to load the data
def load_feed_data(feed_name):

    files = sorted(
        list(glob(f"{config.df_path}/*.csv"))
            | where(lambda x: config.binance_symbol in x)
            | where(lambda x: feed_name in x)
    )

    return pd.read_csv(files[-1])


def load_data(config):
    dfs = []

    for feed_name in config.feed_names:
        df = load_feed_data(feed_name)
        # plot seconds as a bar chart
        df.plot.bar(x="timestamp", y="seconds")
        dfs.append(df)

    df = pd.concat(dfs)
    df = df.sort_values("timestamp")
    df.fillna(method="ffill", inplace=True)
    
    df = df[["timestamp", "close", "0_tick-500_volume-0_time-10_ma", "0.01_tick-0_volume-0_time-10_ma"]]
    df.drop_duplicates(subset="timestamp", inplace=True)

    return df

df = load_data(config)
df.dropna(inplace=True)

df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
df.set_index('datetime', inplace=True)


#====================================
# Create the strategy
#====================================

price = df["close"]
entries = df["0.01_tick-0_volume-0_time-10_ma"] < df["0_tick-500_volume-0_time-10_ma"]
exits = df["0.01_tick-0_volume-0_time-10_ma"] > df["0_tick-500_volume-0_time-10_ma"]

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=1000, freq='1m', direction='both')

print(pf.stats())
pf.plot().show()



