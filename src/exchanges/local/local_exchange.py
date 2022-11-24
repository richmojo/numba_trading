from datetime import datetime
import numpy as np

from src.exchanges.base_exchange import BaseExchange
from src.strats.base_strategy._named_tuples import ExchangeState
import src.exchanges.local._numba as nb


class LocalExchange(BaseExchange):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.symbol = config.ftx_symbol
        self.leverage = config.leverage

        self.position = 0
        
        if config.starting_balance is None:
            self.account_value = 1000
            self.wallet_usd = 1000
        else:   
            self.account_value = config.starting_balance
            self.wallet_usd = config.starting_balance
        
        self.open_trades = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        self.closed_trades = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

        self.fee = config.fee
    
    
    def place_trade(self, state):
       
        # place new trade
        (
            self.open_trades, 
            self.closed_trades, 
            self.account_value, 
            self.avg_entry, 
            self.leverage, 
            self.position, 
            self.wallet_usd
        ) = nb.place_trade( 
            open_trades=self.open_trades, 
            closed_trades=self.closed_trades, 
            account_value=self.account_value, 
            avg_entry=self.avg_entry, 
            fee=self.fee,
            leverage=self.leverage, 
            position=self.position, 
            price=state.price,
            timestamp=state.timestamp,
            trade=state.trade,
            wallet_usd=self.wallet_usd
        )
        
        return state        


    def update_account_values(self, state, exchange_state):
        # calculate open pnl
        open_pnl = 0
        self.avg_entry = state.price

        if len(self.open_trades[self.open_trades[:, 0] != 0]) != 0:
            self.avg_entry = np.average(self.open_trades[:, 0], weights=self.open_trades[:, 2])
            open_pnl = np.sum(self.open_trades[:, 2] * (state.price - self.open_trades[:, 0]))

        # add open pnl to wallet
        self.account_value = self.wallet_usd + open_pnl

        starting_balance = exchange_state.starting_balance
        max_position = exchange_state.max_position

        t = datetime.fromtimestamp(state.timestamp)

        if (t.hour == 3 and t.minute == 5) or (t.hour == 15 and t.minute == 5) or exchange_state.max_position is None:
            starting_balance = self.account_value
            max_position = (self.leverage * starting_balance) / state.price

        return ExchangeState(
            account_value=self.account_value,
            avg_entry=self.avg_entry,
            leverage=self.leverage,
            max_position=max_position,
            position=self.position,
            starting_balance=starting_balance,
            wallet_usd=self.wallet_usd,
        )


        


