import pandas as pd
import numpy as np


class LocalMixin:
    def save_csv(self, state, params):
        """
        Save the data to a csv.
        """
        # load data
        try:
            df = pd.read_csv(f"{self.csv_path}/{state.symbol}_{state.subaccount}_state.csv")
        except:
            df = pd.DataFrame([])

        try:
            params_df = pd.read_csv(f"{self.csv_path}/{state.symbol}_{state.subaccount}_params.csv")
        except:
            params_df = pd.DataFrame([])

        # add new state row
        new_row = pd.DataFrame([state])
        df = pd.concat([df, new_row], ignore_index=True)
        
        #save the last thirty days of data
        df.iloc[-int(30*1440): ].to_csv(f"{self.csv_path}/{state.symbol}_{state.subaccount}_state.csv", index=False)

        # add new params row
        new_row = pd.DataFrame([params])
        params_df = pd.concat([params_df, new_row], ignore_index=True)

        #save the last ten params
        params_df.iloc[-10: ].to_csv(f"{self.csv_path}/{state.symbol}_{state.subaccount}_params.csv", index=False)
