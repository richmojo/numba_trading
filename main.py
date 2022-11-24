import ray
from src.strats.simple_ma.ray_tasks import start_live, start_backtest


# non default params
backtest_days = 100
paper = True

symbols = ["AVAX/USDT", "ETH/USDT", "SOL/USDT"]

# name, leverage
subaccounts = [
    ["test1", 1.0],
]


def run():
    ray.init()
    results = ray.get(
        [
            start_backtest.remote(
                symbol=symbol, backtest_days = backtest_days, fresh_data=True, paper=paper, subaccounts=subaccounts
            )
            for symbol in symbols
        ]
    )


if __name__ == "__main__":
    run()
