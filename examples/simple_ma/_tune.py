from pathlib import Path

path = str(Path(__file__))
path = path.split("/src")[0]

from ray import tune
from ray.tune.suggest.optuna import OptunaSearch

from src.strats.simple_ma.config import Config
from src.strats.simple_ma.dataloader import DataLoader
from src.strats.simple_ma.bot import Bot
from src.strats.simple_ma.ray_tasks import *



def tune_backtest(config):
    fresh_data = False
    # load config
    conf = Config(
        symbol=config["symbol"],
        backtest_days=config["backtest_days"],
        exchange_name=config["exchange"],
        fresh_data=fresh_data,
        leverage=config["leverage"],
        logger_name="backtest",
        ma_window=config["ma_window"],
        mode="backtest",
        tune_bool=True,
    )

    # load data
    dl = DataLoader(conf)

    for feed_name in conf.feed_names:
        dl.save_data(feed_name)

    # run bots
    bot = Bot(conf)
    result = bot.start()

    end_value = result.iloc[-1]["End Value"]

    tune.report(end_value=end_value)


# update the alternate bars that will be used in the backtest

config = dict(
    symbol="SOL/USDT",
    backtest_days=100,
    exchange="local",
    leverage=1,#tune.randint(1),
    ma_window=tune.randint(5, 15),
    mode="backtest",
)

ray.get(download_data.remote(Config(**config)))
ray.get([update_feed_data.remote(Config(**config), feed_name) for feed_name in config["feed_names"]])

tune_dir = f"{path}/data/tune_results"
Path(tune_dir).mkdir(parents=True, exist_ok=True)

analysis = tune.run(
    tune_backtest,
    config=config,
    local_dir=tune_dir,
    metric="end_value",
    mode="max",
    search_alg=OptunaSearch(),
    num_samples=10
)

print(analysis.best_config)


