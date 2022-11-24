import ray
from src.strats.simple_ma.dataloader import DataLoader
from src.strats.simple_ma.config import Config
from src.strats.simple_ma.bot import Bot


# ====================================
# Ray tasks to run backtest
# ====================================


@ray.remote
def download_data(config, live=False):
    dl = DataLoader(config)
    dl.get_trades(live)


@ray.remote
def update_feed_data(config, feed_name):
    dl = DataLoader(config)
    dl.convert_to_bars(feed_name)
    dl.save_data(feed_name)


@ray.remote(num_gpus=0.25, max_calls=1)
def prepare_backtest_gpu(config):
    # update data
    ray.get(download_data.remote(config))

    # update feed data
    ray.get(
        [
            update_feed_data.remote(config, feed_name)
            for feed_name in config.feed_names
        ]
    )


@ray.remote
def prepare_backtest_cpu(config):
    # update data
    ray.get(download_data.remote(config))

    # update feed data
    ray.get(
        [
            update_feed_data.remote(config, feed_name)
            for feed_name in config.feed_names
        ]
    )


@ray.remote
def start_live_feeds(config):
    dl = DataLoader(config)
    dl.start_live_feeds()


@ray.remote
def run_bots(configs):
    # make list if not already
    if not isinstance(configs, list):
        configs = [configs]
    
    bots = [Bot(config) for config in configs]
    [bot.start() for bot in bots]


@ray.remote
def start_backtest(
    symbol,
    backtest_days=5,
    exchange="local",
    fee=0.001,
    force_close=False,
    force_long=False,
    force_short=False,
    fresh_data=False,
    logger_name="backtest",
    ma_window=20,
    mode="backtest",
    paper=False,
    subaccounts=None,
):
    paper=False
    # load configs
    configs = [
        Config(
            symbol=symbol,
            backtest_days=backtest_days,
            exchange_name=exchange,
            fee=fee,
            force_close=force_close,
            force_long=force_long,
            force_short=force_short,
            fresh_data=fresh_data,
            leverage=leverage,
            logger_name="backtest",
            ma_window=ma_window,
            mode=mode,
            paper=paper,
            subaccount=subaccount,
        )
        for subaccount, leverage in subaccounts
    ]

    if fresh_data:
        ray.get(prepare_backtest_gpu.remote(configs[0]))

    _ = ray.get([run_bots.remote(configs)])


# ====================================
# Ray tasks to run live
# ====================================


@ray.remote
def start_live(
    symbol,
    exchange="ftx",
    force_close=False,
    force_long=False,
    force_short=False,
    fresh_data=False,
    logger_name="live",
    ma_window=20,
    mode="live",
    paper=False,
    subaccounts=[[None, 1]],
):
    fresh_data = True
    # load configs
    configs = [
        Config(
            symbol=symbol,
            exchange_name=exchange,
            force_close=force_close,
            force_long=force_long,
            force_short=force_short,
            fresh_data=fresh_data,
            leverage=leverage,
            logger_name=logger_name,
            ma_window=ma_window,
            mode=mode,
            paper=paper,
            subaccount=subaccount,
        )
        for subaccount, leverage in subaccounts
    ]

    config = configs[0]
    # update data
    
    ray.get(download_data.remote(config))
    
    # run in background, to collect data while live
    download_data.remote(config, live=True)

    # start the live feed
    start_live_feeds.remote(config)

    while True:
        try:
            _ = ray.get([run_bots.remote(configs)])
        except Exception as e:
                try:
                    config.logger.send_error(f"Restarting bots: {e}")
                except:
                    print(f"Restarting bots: {e}")
