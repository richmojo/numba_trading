import time
from datetime import datetime
from glob import glob

import pandas as pd
from pipe import where

from src.exchanges.load_exchange import load_exchange

class BaseBot:
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
            - I usually will have one feed that is the most important and will trigger the event
                - For example, if I am trading on the 1m timeframe, I will use the 1m feed to trigger the event
                - And maybe also have a higher timeframe (could be based on percent, ticks, volume etc.) feed that will give a macro view
                    - But this doesnt actually drive starting a new step
        """
        raise NotImplementedError


    def get_feed_glob(self):
        files = sorted(
            list(glob(f"{self.df_path}/*.csv")
                | where(lambda x: self.binance_symbol in x)
            )
        )

        return files


    def get_feeds(self):
        files = glob(f"{self.df_path}/*.csv")
        files = [file for file in files if self.binance_symbol in file]
        feeds = [file.split("/")[-1].split("_")[1:-1] for file in files]
        feeds = ["_".join(feed) for feed in feeds]
        feeds = sorted(list(set(feeds)))

        return feeds


    def load_feed_data(self, feed_name):
        for attempt in range(3):
            try:
                files = sorted(
                    list(glob(f"{self.df_path}/*.csv"))
                        | where(lambda x: self.binance_symbol in x)
                        | where(lambda x: feed_name in x)
                )

                return pd.read_csv(files[-1])
                
            except:
                time.sleep(1)
        else:
            raise Exception("Couldn't load data")


    def get_step_data(self):
        raise NotImplementedError

    
    def get_backtest_data(self):
        raise NotImplementedError


    def start(self):
        if self.mode == "backtest":
            df = self.get_backtest_data()
            
            start = datetime.fromtimestamp(df.iloc[0]["timestamp"])
            end = datetime.fromtimestamp(df.iloc[-1]["timestamp"])
            print(f"Backtesting from {start} : {end}")

            df = df.to_numpy()
            
            for row in df:
                self.step(row)

            try:
                self.logger.finalize(self.binance_symbol, self.exchange.closed_trades)
            except Exception as e:
                print(e)

            return self.logger.stats

        else:
            while True:
                try:
                    self.step()
                    self.ready()
                except Exception as e:
                    try:
                        self.logger.send_error(e)
                    except Exception as e:
                        print(e)


