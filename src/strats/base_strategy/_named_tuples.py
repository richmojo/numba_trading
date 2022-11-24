from typing import NamedTuple
import time
import numpy as np


class AlgoState(NamedTuple):
    """
    AlgoState is a NamedTuple that contains the state of the algorithm
    at a given time. It is used to pass information.
    
    For the backtesting engine to work, the state must contain the following:

    Attributes  
    ----------
    price : float
        The current price of the asset
    timestamp : float
        The current timestamp
    trade : float
        The current trade size

    Other variables can be added to the state, but they are not required.
    """

    price: float=None
    timestamp: int=int(time.time())
    trade: float=0.0

class ExchangeState(NamedTuple):
    """
    Used to save everything from the exchange

    Attributes
    ----------
    account_value : float
        The total value of the account in USD
    avg_entry : float
        The average entry price of the position
    max_position : float
        The maximum position size
    position : float
        The current position of the algorithm
    starting_balance : float
        The starting balance of the account, this is what the max position will be based on
    wallet_usd : float
        The current value of the wallet in USD without unrealized PnL
    """
    account_value: float=None
    avg_entry: float=0.0
    leverage: float=1.0
    max_position: float=None
    position: float=0.0
    starting_balance: float=1000.0
    wallet_usd: float=None





