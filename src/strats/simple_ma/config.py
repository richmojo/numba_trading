from dataclasses import dataclass
from datetime import datetime

from src.strats.base_strategy.base_config import BaseConfig
from src.strats.simple_ma._named_tuples import *

import ccxt

exchange = ccxt.binance({"enableRateLimit": True})

@dataclass
class Config(BaseConfig):
    """
    - Inherits from BaseConfig
        (
            backtest_days, coins_trading, exchange_name, 
            force_close, force_long, force_short, fresh_data, 
            leverage, logger, mode, paper, starting_balance, subaccount, symbol
        )
    - add additional config variables
    """

    ma_window: int = 20
    feed_names: list = None

    def __post_init__(self):
        self.feed_names = [
            "0_tick-500_volume-0_time-10",
            "0.01_tick-0_volume-0_time-10",
        ]

        self.exchange_state = ExchangeState(
            leverage=self.leverage, starting_balance=self.starting_balance
        )

        self.params = Params(
            execution_algo="limit",
            force_close=self.force_close,
            force_long=self.force_long,
            force_short=self.force_short,
            leverage=self.leverage,
            ma_window=self.ma_window,
            paper=self.paper,
        )

        self.state = State(
            price=None,
            subaccount=self.subaccount,
            symbol=self.symbol,
            timestamp=int(time.time()),
            trade=0.0,
            trade_type="no_trade",
        )

        self.set_data_paths()
        self.base_post_init()