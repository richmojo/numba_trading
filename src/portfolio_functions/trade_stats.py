import numpy as np
import pandas as pd
import numba as nb

from empyrical import sharpe_ratio, calmar_ratio, omega_ratio, sortino_ratio

@nb.njit
def max_drawdown(returns):
    max_drawdown = 0
    max_value = 0

    for i in range(len(returns)):
        if returns[i] > max_value:
            max_value = returns[i]
        else:
            drawdown = (max_value - returns[i]) / max_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    return max_drawdown

def trade_stats(trades: pd.DataFrame, account: pd.DataFrame) -> pd.DataFrame:
    trades["entry_datetime"] = pd.to_datetime(trades["entry_time"], unit="s")
    trades["pnl_percent"] = round((trades["exit_price"] / trades["entry_price"] - 1 ) * np.sign(trades["size"]) * 100, 2)
    daily_returns = trades.set_index('entry_datetime').resample('D')['pnl'].sum()

    columns = [
            "Start", "End", "Period", "Start Value", "End Value",
            "Total Return [%]",
            "Total Trades", "Time in trades [%]", "Win Rate [%]", "Best Trade [%]", "Worst Trade [%]",
            "Avg. Winninng Trade [%]", "Avg. Losing Trade [%]", "Profit Factor",
            "Sharpe Ratio", "Calmar Ratio", "Omega Ratio", "Sortino Ratio"
    ]
    
    if len(trades) == 0:
        return

    start = pd.to_datetime(account.iloc[0]["timestamp"], unit="s")
    end = pd.to_datetime(account.iloc[-1]["timestamp"], unit="s")
    period = end - start
    start_value = account.iloc[0]["account_value"]
    end_value = account.iloc[-1]["account_value"]
    total_return = (end_value - start_value) / start_value * 100
    total_trades = len(trades)
    time_in_trades = len(account[account["position"] != 0]) / len(account) * 100
    win_rate = len(trades[trades["pnl"] > 0]) / len(trades) * 100
    best_trade = trades["pnl_percent"].max()
    worst_trade = trades["pnl_percent"].min()
    avg_winning_trade = trades[trades["pnl"] > 0]["pnl_percent"].mean()
    avg_losing_trade = trades[trades["pnl"] < 0]["pnl_percent"].mean()
    profit_factor = trades[trades["pnl"] > 0]["pnl"].sum() / abs(trades[trades["pnl"] < 0]["pnl"].sum())
    sr = sharpe_ratio(daily_returns)
    cr = calmar_ratio(daily_returns)
    omr = omega_ratio(daily_returns)
    sor = sortino_ratio(daily_returns)

    output = [
        [
            start, end, period, start_value, end_value,
            total_return,
            total_trades, time_in_trades, win_rate, best_trade, worst_trade,
            avg_winning_trade, avg_losing_trade, profit_factor,
            sr, cr, omr, sor
        ]
    ]

    stats = pd.DataFrame(output, columns=columns)

    return stats