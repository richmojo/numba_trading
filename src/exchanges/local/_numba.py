from numba import njit
import numpy as np


@njit
def place_trade(
    open_trades: np.ndarray,
    closed_trades: np.ndarray,
    account_value: float,
    avg_entry: float,
    fee: float,
    leverage: float,
    position: float,
    price: float,
    timestamp: int,
    trade: float,
    wallet_usd: float,
):

    open_trades = open_trades[open_trades[:, 0] != 0]
    closed_trades = closed_trades[closed_trades[:, 1] != 0]

    state_trade_size = trade

    """
        Example trade:
            [entry_price, exit_price, size, pnl, entry_time, exit_time, fees]

    """

    # new trade
    if position == 0:
        new_trade = np.array(
            [
                [
                    price,
                    0.0,
                    trade,
                    0,
                    timestamp,
                    0.0,
                    0.0,
                ]
            ]
        )

        if open_trades.any():
            open_trades = np.vstack((open_trades, new_trade))
        else:
            open_trades = new_trade

    else:
        # increase trade size, add trade to open trades
        if np.sign(trade) == np.sign(position):
            new_trade = np.array(
                [
                    [
                        price,
                        0.0,
                        trade,
                        0.0,
                        timestamp,
                        0.0,
                        0.0,
                    ]
                ]
            )

            if open_trades.any():
                open_trades = np.vstack((open_trades, new_trade))
            else:
                # reshape to 2d array
                open_trades = new_trade

        # close trade
        else:
            for i in range(len(open_trades)):
                t = open_trades[i]

                t_entry = t[0]
                t_exit = t[1]
                t_size = t[2]
                t_pnl = t[3]
                t_entry_time = t[4]
                t_exit_time = t[5]
                t_fees = t[6]

                # partial close of current trade in open trades
                if abs(trade) < abs(t_size):
                    new_trade = np.array(
                        [
                            [
                                t_entry,
                                price,
                                abs(trade) * np.sign(t_size),
                                0,
                                t_entry_time,
                                timestamp,
                                0,
                            ]
                        ]
                    )

                    # add fees to trade
                    new_trade[0][6] = (
                        fee * abs(new_trade[0][2]) * new_trade[0][0]
                        + fee * abs(new_trade[0][2]) * new_trade[0][1]
                    )

                    # add pnl
                    new_trade[0][3] = (new_trade[0][1] - new_trade[0][0]) * new_trade[0][2] - new_trade[0][
                        6
                    ]

                    if closed_trades.any():
                        closed_trades = np.vstack((closed_trades, new_trade))
                    else:
                        closed_trades = new_trade

                    wallet_usd += new_trade[0][3]

                    # update open trade to remainder
                    open_trades[i][2] = t_size + trade

                # fully closing open trade in loop with more to be closed
                elif abs(trade) > abs(t_size):
                    new_trade = np.array(
                        [
                            [
                                t_entry,
                                price,
                                t_size,
                                0,
                                t_entry_time,
                                timestamp,
                                0,
                            ]
                        ]
                    )

                    # add fees to trade
                    new_trade[0][6] = (
                        fee * abs(new_trade[0][2]) * new_trade[0][0]
                        + fee * abs(new_trade[0][2]) * new_trade[0][1]
                    )

                    # add pnl
                    new_trade[0][3] = (new_trade[0][1] - new_trade[0][0]) * new_trade[0][2] - new_trade[0][
                        6
                    ]

                    if closed_trades.any():
                        closed_trades = np.vstack((closed_trades, new_trade))
                    else:
                        closed_trades = new_trade

                    wallet_usd += new_trade[0][3]

                    # update trade to remainder
                    state_trade_size += t_size

                # fully closing open trade with matching trade size
                else:
                    new_trade = np.array(
                        [
                            [
                                t_entry,
                                price,
                                t_size,
                                0,
                                t_entry_time,
                                timestamp,
                                0,
                            ]
                        ]
                    )

                    # add fees to trade
                    new_trade[0][6] = (
                        fee * abs(new_trade[0][2]) * new_trade[0][0]
                        + fee * abs(new_trade[0][2]) * new_trade[0][1]
                    )

                    # add pnl
                    new_trade[0][3] = (new_trade[0][1] - new_trade[0][0]) * new_trade[0][2] - new_trade[0][
                        6
                    ]

                    if closed_trades.any():
                        closed_trades = np.vstack((closed_trades, new_trade))
                    else:
                        closed_trades = new_trade

                    wallet_usd += new_trade[0][3]

                    state_trade_size = 0

            open_trades = open_trades[open_trades[:, 1] != 0]

            # open new trade if there is a remainder
            if state_trade_size != 0 and len(open_trades) == 0:

                new_trade = np.array(
                    [[price, 0.0, state_trade_size, 0, timestamp, 0.0, 0.0]]
                )

                open_trades = new_trade

    if len(open_trades) == 0:
        avg_entry = price
        position = 0
        open_trades = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    else:
        avg_entry = np.average(open_trades[:, 0], weights=open_trades[:, 2])
        position = np.sum(open_trades[:, 2])

    if len(closed_trades) == 0:
        closed_trades = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    return (
        open_trades,
        closed_trades,
        account_value,
        avg_entry,
        leverage,
        position,
        wallet_usd,
    )
