from src.logging.backtest_logger import BacktestLogger
from src.logging.live_logger import LiveLogger


def load_logger(logger):
    if logger == "backtest":
        return BacktestLogger()
    elif logger == "live":
        return LiveLogger()
    else:
        raise Exception("Invalid mode")