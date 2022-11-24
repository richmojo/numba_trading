
from numba import njit
import numba as nb

import numpy as np
import pandas as pd

#====================================
# Basic Alternate Tick Bars
#====================================

@njit
def alt_tick_bars(df_data, agg_data, freqs):
    """
    Convert data to bars based on time, ticks, volume, and percent change

    Parameters
    ----------
    data : np.array
        -prices | volume | costs | side: 1 or -1 | timestamps | seconds

    agg_data : np.array
        -open_price | high_price | low_price | volume | buy_volume | sell_volume | buy_cost | sell_cost | ticks | buy_ticks | sell_ticks | open_time: total seconds

    freqs : np.array
        -tick_freq | percent_freq | volume_freq | time_freq
    """
    
    # set df_data
    prices = df_data[0]
    volumes = df_data[1]
    costs = df_data[2]
    sides = df_data[3]
    timestamps = df_data[4]
    seconds = df_data[5]

    # set agg_data
    open_price = agg_data[0]
    high_price = agg_data[1]
    low_price = agg_data[2]
    volume = agg_data[3]
    buy_volume = agg_data[4]
    sell_volume = agg_data[5]
    buy_cost = agg_data[6]
    sell_cost = agg_data[7]
    ticks = agg_data[8]
    buy_ticks = agg_data[9]
    sell_ticks = agg_data[10]
    open_time = agg_data[11]

    # set freqs
    tick_freq = freqs[0]
    percent_freq = freqs[1]
    volume_freq = freqs[2]
    time_freq = freqs[3]

    bars = None
    length = len(prices)

    for i in range(length):
        if sides[i] == 1:
            buy_volume += volumes[i]
            buy_cost += costs[i]
            buy_ticks += 1

        else:
            sell_volume += volumes[i]
            sell_cost += costs[i]
            sell_ticks += 1

        high_price = prices[i] if prices[i] > high_price else high_price
        low_price = prices[i] if prices[i] < low_price else low_price
        volume += volumes[i]
        ticks += 1
        open_time += seconds[i]

        spread = np.abs((prices[i] / open_price) - 1)

        if (
            (tick_freq == 0 or ticks >= tick_freq)
            and (percent_freq == 0 or spread >= percent_freq)
            and (volume_freq == 0 or volume >= volume_freq)
            and (time_freq == 0 or open_time >= time_freq)
            and ticks != 0
        ):
            bar = [
                open_price,
                high_price,
                low_price,
                prices[i],
                buy_volume,
                sell_volume,
                buy_cost,
                sell_cost,
                buy_ticks,
                sell_ticks,
                open_time,
                timestamps[i],
            ]

            if bars is None:
                bars = nb.typed.List()
                bars.append(bar)
            else:
                bars.append(bar)

            open_price = prices[i]
            high_price = prices[i]
            low_price = prices[i]
            volume = 0
            buy_volume = 0
            sell_volume = 0
            buy_cost = 0
            sell_cost = 0
            ticks = 0
            buy_ticks = 0
            sell_ticks = 0
            open_time = 0

    agg_data = np.array(
        [
            open_price,
            high_price,
            low_price,
            volume,
            buy_volume,
            sell_volume,
            buy_cost,
            sell_cost,
            ticks,
            buy_ticks,
            sell_ticks,
            open_time,
        ]
    )

    return bars, agg_data
