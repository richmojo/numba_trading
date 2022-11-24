# Numba Trading

    Live and backtesting library that uses numba and ray for speed and parallelism.

This is an example of the way I do my live trading. If I was really making a strategy as simple as the example I show here I would probably not use something this confusing/complex but for my strategy this was as simple as I could get it. 

I wouldnt recommend using this for anything other than the as a sample guide for developing your own library. A lot of this proabably won't be needed for your strategy and your strategy might need things that this doesnt provide.

This repo more than likely won't be updated.

# Basic Framework

### Each strategy contains the following:

- config.py
  - This is where you set all the parameters for the strategy
- dataloader.py
  - This is used to load the data for backtests and live trading
- bot.py
  - This is the main class that runs the strategy
- ray_tasks.py
  - This is where you define the tasks that will be run in parallel.
  - The reason I'm using tasks instead of actors is it just made it easier to use my GPU. When using an actor, which is just adding the ray decorator to a class, the GPU wouldn't release the memory after the task was done. I couldn't figure out how to fix this so I just used tasks instead.
- \_named_tuples.py
  - This is where you define the named tuples that will be used to store data
  - I use named tuples because they are easy to pass to numba
- \_numba.py
  - This is where you define all the numba functions. I make everything that doesnt invole an api call a numba function
  - Completely unecessary for this strategy and probably for most higher time frame strategies but it doenst hurt to speed things up and its not hard to do.
  - Advice for using numba, first make sure it works without the @njit decorator and then add it. The biggest problem I have is with datatype. You need to tell it what everything is.
- \_tune.py (optional)

  - This is where you define the hyperparameters that you want to tune and the ranges you want to tune them in.

- \_vectorbt.py (optional)
  -Easy way to use vectorized backtesting. I just use this to quickly test out things without having to make a complete live pipeline.

# Improvements

- Switch to a using a database instead of flat files for data storage
- Integrate more vectorbt features. I've copied some of the trade stats stuff but I'd like to completely integrate their portfolio to be able to use all the functions they have associated with it.
- Change the way tune runs. Right now it saves a new dataframe for each iteration. This is fine for a small number of iterations but it would be better to save the results to a database and then just load the results from the database. Or even just use csv's but reuse them based on parameters.

# Usage

```python
    import ray
    from src.strats.simple_ma.dataloader import DataLoader
    from src.strats.simple_ma.config import Config
    from src.strats.simple_ma.bot import Bot
    from src.logging.backtest_logger import BacktestLogger
    from src.strats.simple_ma.ray_tasks import start_backtest, start_live

    # Sample backtest

    symbols =[ "BTC/USDT", "ETH/USDT"]
    backtest_days = 10
    fee = 0.001
    results = ray.get([start_backtest.remote(symbol=symbol, backtest_days=backtest_days, fee=fee) for symbol in symbols])


    # Sample live
    """
    The live code may have some bugs, I switched a few things and because I used FTX
    I can't check to see if everything runs correctly.
    """

    symbols =[ "BTC/USDT", "ETH/USDT"]
    
    # name, leverage
    subaccounts = [
        ["test1", 1.0],
        ["test2", 2.0]
    ]

    results = ray.get([start_live.remote(symbol=symbol, subaccounts=subaccounts) for symbol in symbols])
```

# Docker for live deployment

```python
    # Run docker compose
    docker-compose up -d
```

# Streamlit app for viewing backtest

```python
    # Run streamlit app
    streamlit run [path]/numba_trading/src/streamlit_apps/backtest_results.py
```

![alt text](https://github.com/jrich10/numba_trading/blob/main/src/streamlit_apps/demo_files/backtest_results_demo.gif)
