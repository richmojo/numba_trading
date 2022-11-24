from src.logging.base_logger import Logger
from src.logging.mixins.local_mixin import LocalMixin
from src.portfolio_functions.trade_stats import trade_stats


from pathlib import Path
import time
import pandas as pd
import random

path = str(Path(__file__))
path = path.split("/src")[0]


class BacktestLogger(Logger, LocalMixin):
    def __init__(self) -> None:
        """
        Initialize the Influx logger.
        """
        super().__init__()
        
        self.data = []

        self.csv_path = f"{path}/data/backtest_results"

        Path(self.csv_path).mkdir(parents=True, exist_ok=True)

    def end_of_step(self, logging_state, params):
        """
        Save the state of the backtest.
        """
        self.data.append(logging_state)

        return params


    def finalize(self, symbol, trades) -> None:
        """
        Finalize the data, this will be called at the end of backtesting.
        Not used live.
        """

        print("Saving backtest")
        id = f"{symbol}_{int(time.time())}_{random.randint(0, 1000)}"

        # create directory for backtest
        Path(self.csv_path).mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(self.data)
        df.to_csv(f"{self.csv_path}/{id}_backtest.csv", index=False)
        
        trades = pd.DataFrame(trades, columns = ["entry_price", "exit_price", "size", "pnl", "entry_time", "exit_time", "fees"])
        trades.to_csv(f"{self.csv_path}/{id}_trades.csv", index=False)

        self.stats = trade_stats(trades, df)
        self.stats.to_csv(f"{self.csv_path}/{id}_stats.csv", index=False)

        print(self.stats.iloc[0])       

