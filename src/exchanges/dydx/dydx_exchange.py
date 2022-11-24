import os
from datetime import datetime
from dydx3 import Client

from dotenv import load_dotenv
load_dotenv()

from src.exchanges.base_exchange import BaseExchange
from src.strats.base_strategy._named_tuples import ExchangeState
from src.exchanges.dydx.account_info import AccountInfo
from src.exchanges.dydx.orders_mixin import OrdersMixin



class Dydx(BaseExchange, AccountInfo, OrdersMixin):
    def __init__(self, config):
        super().__init__()

        self.config = config
        self.logger = self.logger

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

        # change key based on subaccount in future using separate .env files
        
        client = Client(
            host="https://api.dydx.exchange",
            default_ethereum_address=os.environ.get("DYDX_ETH_ADDRESS"),
            eth_private_key=os.environ.get("DYDX_SECRET_KEY"),
        )

        start_private_key = client.onboarding.derive_stark_key()['private_key']

        self.exchange = Client(
            host="https://api.dydx.exchange",
            default_ethereum_address=os.environ.get("DYDX_ETH_ADDRESS"),
            eth_private_key=os.environ.get("DYDX_SECRET_KEY"),
            stark_private_key=start_private_key,
        )

        self.position_id = self.exchange.private.get_account().data['account']['positionId']

        self.update_account_values()
        self.market_specs()

    def place_trade(self, state):
        if self.execution_algo == "chase_limit_order":
            self.chase_limit_order(state)

    def update_account_values(self, state=None, exchange_state=None):
        try:           
            self.position = self.get_position()
            self.account_value = self.get_account_balance() / self.coins_trading
            if self.position == 0:
                self.wallet_usd = self.account_value

            self.price = self.get_price(self.symbol)
            self.starting_balance = self.account_value
            self.subaccount_balance = self.get_account_balance()
            self.max_position = self.get_max_position()       

            if state is not None:
                self.avg_entry = self.price if self.position == 0 else self.avg_fill_price(self.symbol, self.price)
                t = datetime.fromtimestamp(state.timestamp)
                if (t.hour == 3 and t.minute == 5) or (t.hour == 15 and t.minute == 5) or exchange_state.max_position is None:
                    self.starting_balance = self.account_value
                    self.max_position = (self.leverage * self.starting_balance) / self.price

            return ExchangeState(
                account_value=self.account_value,
                avg_entry=self.avg_entry,
                leverage=self.leverage,
                max_position=self.max_position,
                position=self.position,
                starting_balance=self.starting_balance,
                wallet_usd=self.wallet_usd,
            )
        except Exception as e:
            self.logger.send_trade_info(f"Could not update account values with error: {e}")
            return exchange_state
