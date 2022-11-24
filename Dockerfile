FROM python:3.10

WORKDIR /numba_trading

COPY ./requirements.txt /numba_trading/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /numba_trading


CMD ["python", "main.py"]