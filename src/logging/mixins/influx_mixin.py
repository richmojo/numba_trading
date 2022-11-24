from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from src.logging.base_logger import data_to_string

class InfluxFunctions:
    """
    Mixin to handle influxdb calls
    """

    def save_state(self, state):
        try:
            """
            Just an example of how you could save the state to influxdb. 
            I would save individual fields as well.
            """
            string = data_to_string(state)

            p = ( 
                Point("algo_state")
                .tag("symbol", str(state.symbol))
                .field("state_string", str(string))
            )

            write_api = self.client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket="mltrader_data", record=p)   

            del state

        except Exception as e:
            message = f"save_state: {e}"
            self.send_error_to_influx(message)
            print(message)

    def load_state(self, state):
        """
        Need to implement this based on what you need
        """
        raise NotImplementedError
    def save_params(self, params):
        """
        Need to implement this based on what you need
        """
        raise NotImplementedError

    def load_params(self, params):
        """
        Need to implement this based on what you need
        """
        raise NotImplementedError

    def send_error_to_influx(self, error):
        try:
            error_type = error.split(" ")[0]
        
            p = (
                Point("error")
                .tag("error_type", str(error_type))
                .field("error_message", str(error))
            )

            write_api = self.client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket="mltrader_errors", record=p)
        except Exception as e:
            print(error, e)