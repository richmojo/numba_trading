# Loggers

The `logging` module provides a simple logging API for saving and recording data.

# I currently show 2 here

## Backtesting
- `BacktestLogger` - This is used to log data for backtesting. Right now I just have it where I log the data to a csv file.

## Live
- `LiveLogger` - This is used to log data for live trading. When live I usually log to discord, a csv, and InfluxDB. I use InfluxDB to store the data and then I use Grafana to display it. Discord is used to have a simple way to see its running and to get alerts when theres an error. And then the csv is used for a streamlit app. I like streamlit because it makes it easy to make quick functions in python of things you want to monitor.

I usually will create a new logger based on what the strategy needs.

I use mixins for each different logging method. This is so I can easily reuse the same code for different loggers.