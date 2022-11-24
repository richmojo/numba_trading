from typing import NamedTuple

from src.strats.base_strategy._named_tuples import *

class State(NamedTuple):
    """
    State is a NamedTuple that contains the state of the algorithm
    at a given time. It is used to pass information.
    
    For the backtesting engine to work, the state must contain the following: price, timestamp, trade

    Attributes  
    ----------
    position : float
        The current position of the algorithm
    price : float
        The current price of the asset
    subaccount : str
        The subaccount thats being used if using a subaccount, None uses Main Account on ftx
    symbol : str
        The symbol of the asset being traded
    timestamp : float
        The current timestamp
    trade : float
        The current trade size
    """
    price: float=None
    subaccount: str=None
    symbol: str=None
    timestamp: int=int(time.time())
    trade: float=0.0
    trade_type: str="no_trade"


class Params(NamedTuple):
    """
    Params is a NamedTuple that contains the parameters of the algorithm
    at a given time. It is used to pass information

    Attributes  
    ----------
    execution_algo : str
        The execution algorithm to use while live, ie "limit", "chase_limit", "market", "random_custom_algo"
    force_close : bool
        If True, the algorithm will close the position
    force_long : bool
        If True, the algorithm will go long
    force_short : bool
        If True, the algorithm will go short
    ma_window: int
        The window size for the moving average
    paper : bool
        If True, the algorithm will run in paper mode
    """
    execution_algo: str=None
    force_close: bool=False
    force_long: bool=False
    force_short: bool=False
    leverage: float=1.0
    ma_window: int=20
    paper: bool=False


class LoggingState(NamedTuple):
    """
    Everything I want to record in the logger
    """
    timestamp: int
    price: float
    tick_ma: float
    percent_ma: float
    max_position: float
    position: float
    trade: float
    trade_type: str
    account_value: float
    wallet_usd: float
    
