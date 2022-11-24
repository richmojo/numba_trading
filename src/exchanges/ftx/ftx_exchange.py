import ccxt
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from src.exchanges.base_exchange import BaseExchange
from src.exchanges.ftx.account_info import AccountInfo
from src.exchanges.ftx.executions import Executions
from src.exchanges.ftx.manual import Manual
from src.exchanges.ftx.orders_mixin import OrdersMixin
from src.strats.base_strategy._named_tuples import ExchangeState


class FtxExchange(BaseExchange, OrdersMixin, AccountInfo, Manual, Executions):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = config.logger

        self.account_value = None
        self.coins_trading = config.coins_trading
        self.execution_algo = config.params.execution_algo
        self.leverage = config.leverage
        self.position = None
        self.price = None
        self.subaccount = config.subaccount
        self.subaccount_balance = None
        self.symbol = config.ftx_symbol
        self.wallet_usd = None

        self.exchange = ccxt.ftx(
            {
                "apiKey": os.environ.get("FTX_KEY"),
                "secret": os.environ.get("FTX_SECRET"),
                "timeout": 2000,
                "headers": {
                    "FTX-SUBACCOUNT": self.subaccount,
                },
            }
        )

        self.update_account_values()
        self.market_specs()

    def place_trade(self, state):
        if self.execution_algo == "chase_limit_order":
            self.chase_limit_order(state)

    def update_account_values(self, state=None, exchange_state=None):
        price = state.price
        
        self.position = self.get_position()
        self.account_value = self.get_account_balance() / self.coins_trading
        if self.position == 0:
            self.wallet_usd = self.account_value

        self.current_price = self.get_last_price()
        self.starting_balance = self.account_value
        self.subaccount_balance = self.get_account_balance()
        self.max_position = self.get_max_position()       

        if state is not None:
            self.avg_entry = price if self.position == 0 else self.avg_fill_price(self.symbol, price)
            t = datetime.fromtimestamp(state.timestamp)
            if (t.hour == 3 and t.minute == 5) or (t.hour == 15 and t.minute == 5) or exchange_state.max_position is None:
                self.starting_balance = self.account_value
                self.max_position = (self.leverage * self.starting_balance) / price

        return ExchangeState(
            account_value=self.account_value,
            avg_entry=self.avg_entry,
            leverage=self.leverage,
            max_position=self.max_position,
            position=self.position,
            starting_balance=self.starting_balance,
            wallet_usd=self.wallet_usd,
        )

