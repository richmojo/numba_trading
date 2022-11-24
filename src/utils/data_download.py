import os
import ray
import vectorbt as vbt
from pathlib import Path

path = str(Path(__file__))
path = path.split("/src")[0]

#====================================
# Download data from Binance
#====================================

@ray.remote
def get_data(symbol, timeframe, start, end, save=True):
    """
    Download data from Binance and save it to a CSV file.
    """
    # Download data
    df = vbt.CCXTData.download(
        symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
    ).get()

    save_path = f"{path}/data/bars/{timeframe}"

    symbol = symbol.replace("/", "-")

    # Save to CSV
    try:
        os.mkdir(save_path)
    except:
        pass
    
    if save:
        df.to_csv(f'{save_path}/{symbol}.csv')

    return df



#====================================
# Example Usage
#====================================

# symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# df = ray.get([get_data.remote(symbol, "1h", "2021-01-01", "2022-12-12") for symbol in symbols])
