import streamlit as st

from plotly import graph_objects as go
from plotly import express as px
from plotly.subplots import make_subplots



import pandas as pd
import numpy as np

import time
import datetime
from glob import glob

from pathlib import Path

path = str(Path(__file__))
path = path.split("/numba_trading")[0]

import sys
sys.path.append(f"{path}/numba_trading")

path = str(Path(__file__))
path = path.split("/src")[0]

from src.streamlit_apps.charts.plot_trades import trades

st.set_page_config(
    page_title="Backtest Results",
    page_icon="✅",
    layout="wide",
)

st.title("Backtest Results")

backtest_paths = glob(f"{path}/data/backtest_results/*backtest.csv")
filtered_paths = [file.split("/")[-1].split(".")[0] for file in backtest_paths]


ids = sorted(list(set(filtered_paths)))

bt_ids = st.sidebar.multiselect("Select Backtest Id's", ids)

paths = [p for p in backtest_paths if p.split("/")[-1].split(".")[0] in bt_ids]


def get_data(name) -> pd.DataFrame:
    data = pd.read_csv(name)
    cols = data.columns
    data["datetime"] = pd.to_datetime(data["timestamp"], unit="s")
    data["id"] = name.split("/")[-1].split(".")[0]
    data = data[["datetime"] + list(cols) + ["id"]]
    #data = data.loc[data.trade_type != "no_trade"]
    return data

dfs = [get_data(p) for p in paths]

def plot_av(data):
    fig = px.line(data, x="datetime", y="account_value", color="id")
    fig.update_layout(
        title="Account Value",
        xaxis_title="Date",
        yaxis_title="",
        legend_title="",
        margin=go.layout.Margin(l=0, r=0, b=0, t=25),
    )
    fig.update_xaxes(rangeslider_visible=True)


    st.plotly_chart(fig, use_container_width=True)

if len(dfs) != 0:

    start_times = [data.datetime.min() for data in dfs]
    end_times = [data.datetime.max() for data in dfs]

    start_date = min(start_times)
    end_date = max(end_times)

    start = st.sidebar.date_input("Start Date", start_date, min_value=start_date, max_value=end_date)
    end = st.sidebar.date_input("End Date", end_date, min_value=start_date, max_value=end_date)

    df = pd.concat(dfs)
    df = df.loc[(df['datetime'].dt.date >= start) & (df['datetime'].dt.date <= end)]
    plot_av(df)

else:
    st.write("No data to display")


chart_to_show = st.sidebar.selectbox("Select Chart", ["Empty"] + bt_ids)


def get_full_data(name) -> pd.DataFrame:
    data = pd.read_csv(name)
    cols = data.columns
    data["datetime"] = pd.to_datetime(data["timestamp"], unit="s")
    data = data[["datetime"] + list(cols)]
    return data

# range slider for date
start_date = datetime.date(year=2021,month=1,day=1) #  I need some range in the past
end_date = datetime.datetime.now().date()
max_days = end_date-start_date


if chart_to_show != "Empty":
    try:
        df = get_full_data(f"{path}/data/backtest_results/{chart_to_show}.csv")
        df = df.loc[(df['datetime'].dt.date >= start) & (df['datetime'].dt.date <= end)]

        rows = st.sidebar.number_input("Number of rows", 1, 5, 1)
        columns = []

        if rows > 0:
            col_1 = st.sidebar.multiselect("Select Row 1 Columns", df.columns)
            columns.append(col_1)

        if rows > 1:
            col_2 = st.sidebar.multiselect("Select Row 2 Columns", df.columns)
            columns.append(col_2)
        
        if rows > 2:
            col_3 = st.sidebar.multiselect("Select Row 3 Columns", df.columns)
            columns.append(col_3)
        
        if rows > 3:
            col_4 = st.sidebar.multiselect("Select Row 4 Columns", df.columns)
            columns.append(col_4)
        
        if rows > 4:
            col_5 = st.sidebar.multiselect("Select Row 5 Columns", df.columns)
            columns.append(col_5)

    
        show_trades = st.sidebar.checkbox("Show Trades")

        fig = trades(df, rows, columns, show_trades)
        st.plotly_chart(fig, use_container_width=True)

        # two columns for backtest df and parameters
        col1, col2 = st.columns(2)


        st.dataframe(df)


    except Exception as e:
        st.write(e)

    try:
        stats_to_show = chart_to_show.replace("_backtest", "_stats")
        stats = pd.read_csv(f"{path}/data/backtest_results/{stats_to_show}.csv")
        # create a kpi for each stat
        placeholder = st.empty()
        with placeholder.container():
            for col in stats.columns:
                if type(stats[col].values[0]) == str:
                    st.markdown(f"**{col}**: {stats[col].values[0]}")
                else:
                    st.markdown(f"**{col}**: {round(stats[col].values[0], 2)}")
    except Exception as e:
        st.write(e)

else:
    st.write("# Select a backtest to display")










