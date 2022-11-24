from src.exchanges.local.local_exchange import LocalExchange


def load_exchange(config):
    if config.exchange_name == "local":
        print("Loading local exchange")
        return LocalExchange(config)
    else:
        raise Exception("Invalid mode")