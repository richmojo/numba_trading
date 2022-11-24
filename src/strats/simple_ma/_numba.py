import numpy as np
from numba import njit

from src.strats.simple_ma._named_tuples import State, ExchangeState, Params


@njit
def numba_step(
    row: np.ndarray,
    state: State,
    exchange_state: ExchangeState,
    params: Params,
):

    timestamp, price, tick_ma, percent_ma = row[0], row[1], row[2], row[3]
    trade_type = set_trade_type(row, params)

    if np.logical_or(
        (trade_type != "no_trade" and params.paper == False),
        trade_type == "close"        
    ):
        trade = calc_trade_size(
            exchange_state.max_position,
            exchange_state.position,
            trade_type,
        )

    else:
        trade = 0

    return State(
        price=price,
        subaccount=state.subaccount,
        symbol=state.symbol,
        timestamp=timestamp,
        trade=trade,
        trade_type=trade_type,
    )



@njit
def set_trade_type(
    row: np.ndarray,
    params: Params,
):

    tick_ma, percent_ma = row[2], row[3]
    
    if params.force_close:
        return "close"
    
    if params.force_long:
        return "long"
    
    if params.force_short:
        return "short"


    if tick_ma > percent_ma:
        trade_type = "long"
    elif tick_ma < percent_ma:
        trade_type = "short"
    else:
        trade_type = "no_trade"

    return trade_type


@njit
def calc_trade_size(
    max_position: float,
    position: float,
    trade_type: str,
) -> float:
    """
    Calculate the trade size based on the action, position, and max position.
        - All in, all out
    """

    if trade_type == "close":
        return -position

    if trade_type == "long":
        trade_sign = 1
    
    elif trade_type == "short":
        trade_sign = -1

    if (
        abs(position) >= max_position * 0.95
        and trade_sign == np.sign(position)
    ):
        return 0

    trade_goal = max_position * trade_sign

    return trade_goal - position
