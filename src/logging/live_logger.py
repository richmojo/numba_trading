from src.logging.base_logger import Logger, data_to_string
from src.logging.mixins.influx_mixin import InfluxFunctions
from src.logging.mixins.local_mixin import LocalMixin
from src.logging.mixins.discord_mixin import DiscordMixin
from influxdb_client import InfluxDBClient

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

path = str(Path(__file__))
path = path.split("/src")[0]


class LiveLogger(Logger, InfluxFunctions, LocalMixin, DiscordMixin):
    def __init__(self) -> None:
        """
        Initialize the Influx logger.
        """
        super().__init__()
        
        try:
            self.client = InfluxDBClient(
                url=os.environ.get("INFLUX_ADDRESS"),
                token=os.environ.get("INFLUX_TOKEN"),
                org=os.environ.get("INFLUX_ORG"),
            )
        except:
            self.client = None
            print("No InfluxDB client found. Please check your .env file.")

        self.discord_errors_url = os.environ.get("DISCORD_ERROR")
        self.discord_logs_url = os.environ.get("DISCORD_LOGS")
        self.discord_trades_url = os.environ.get("DISCORD_TRADES")

        self.csv_path = f"{path}/data/logs"

        Path(self.csv_path).mkdir(parents=True, exist_ok=True)

        
    def end_of_step(self, state, params) -> None:
        """
        Save the state and then load the params at the end of the step.
        If you need to change params they can be changed live by updating on influx or any database you use
        """
        self.save_state(state)
        self.save_csv(state, params)
        self.send_discord_logs(data_to_string(state))
        params = self.load_params(params)
        self.save_params(params)

        return params


    def send_error(self, message):
        self.send_discord_errors(message)


    def send_trade_info(self, message):
        self.send_discord_trades(message)