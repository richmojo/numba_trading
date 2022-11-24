class Logger:
    def log_params(self, params) -> None:
        """
        Log the algo params.
        """
        pass

    def end_of_step(self, state) -> None:
        """
        End of step logging.
        """
        pass

    def save(self, data) -> None:
        """
        Save the data.
        """
        pass

    def finalize(self) -> None:
        """
        Finalize the data, this will be called at the end of backtesting.
        Not used live.
        """
        pass



def update_types(d: dict):
    for k, v in d.items():
        if v == 'None':
            d[k] = None
        elif v == 'True':
            d[k] = True
        elif v == 'False':
            d[k] = False
        elif type(v) == str:
            if v.isnumeric():
                d[k] = int(v)
            elif "." in v:
                d[k] = float(v)
        
    return d

def data_to_string(data):
    d = data._asdict()
    string = ""
    for k, v in d.items():
        if type(v) == float:
            v = round(v, 4)
        string += f"{k} = {v}, "
    return string[:-2]


def string_to_dict(string):
    d = {}
    for kv in string.split(", "):
        k, v = kv.split(" = ")
        d[k] = v
        
    return update_types(d)