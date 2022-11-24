from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import ccxt
import os
import time
import random

from src.logging.load_logger import load_logger

path = str(Path(__file__))
path = path.split("/src")[0]

exchange = ccxt.binance({"enableRateLimit": True})

@dataclass
class BaseConfig:
    backtest_days: int = 100
    backtest_results_path = f"{path}/data/backtest_results"
    coins_trading: int = 1
    exchange_name: str = "local"
    fee: float = 0.0
    force_close: bool = False
    force_long: bool = False
    force_short: bool = False
    fresh_data: bool = False
    leverage: int = 1
    logger_name: str = None
    mode: str = "backtest"
    paper: bool = False
    starting_balance: float = None
    subaccount: str = None
    tune_bool: bool = False
    symbol: str = None


    def base_post_init(self):
        self.set_data_paths()

        # formatted symbols
        self.ftx_symbol = self.symbol.replace("/USDT", "-PERP")
        self.binance_symbol = self.symbol.replace("/", "-")

        self.logger = load_logger(self.logger_name)

        # get backtest start timestamp and convert to seconds
        now = datetime.now()
        now = exchange.parse8601(now.strftime("%Y-%m-%dT%H:%M:%S"))        
        days = self.backtest_days * 24 * 3600 * 1000
        self.backtest_start = (now - days) / 1000

        if self.mode == "backtest":
            self.paper = False
    
    def set_data_paths(self):
        """
        1. Function creates the following folders in the data folder:
            a. binance_raw_trades
            b. alternate_bars
            c. dataframes
            d. logs
        2. If the data folder already exists, it deletes the dataframes folder and re-creates it 
        """

        self.alternate_bars_path = f"{path}/data/alternate_bars"
        self.df_path = f"{path}/data/dataframes"
        self.logs_path = f"{path}/data/logs"
        self.raw_trades_path = f"{path}/data/binance_raw_trades"

        if self.tune_bool:
            
            self.df_path = f"{path}/data/dataframes_tune"

        # create paths if they don't exist
        Path(f"{path}/data").mkdir(parents=True, exist_ok=True)
        Path(self.raw_trades_path).mkdir(parents=True, exist_ok=True)
        Path(self.alternate_bars_path).mkdir(parents=True, exist_ok=True)
        Path(self.logs_path).mkdir(parents=True, exist_ok=True)

        # delete dataframes folder
        if self.fresh_data:
            os.system(f"rm -rf {self.df_path}")
        Path(self.df_path).mkdir(parents=True, exist_ok=True)

        if self.tune_bool:
            self.seed = random.randint(0, 1000000)
            self.df_path = f"{self.df_path}/{int(time.time() + self.seed)}"
            Path(self.df_path).mkdir(parents=True, exist_ok=True)
