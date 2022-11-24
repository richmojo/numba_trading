from plotly import graph_objects as go
from plotly import express as px
from plotly.subplots import make_subplots

def trades(df, rows=3, row_columns=[], show_trades=True):

    index = [i for i, _ in enumerate(df["timestamp"])]
    buys = [i for i, x in enumerate(df["trade"]) if x > 0]
    sells = [i for i, x in enumerate(df["trade"]) if x < 0]

    specs = [[{"secondary_y": True}] for _ in range(rows)]

    row_heights = []

    for i in range(rows):
        if i == 0:
            row_heights.append(4)
        else:
            row_heights.append(2)
    
    fig = make_subplots(
        rows=rows,
        row_heights=row_heights,
        specs=specs,
        shared_xaxes=True,
        vertical_spacing=0.05,
    )

    for i, row in enumerate(row_columns):
        for j, col in enumerate(row):
            fig.add_trace(
                go.Scatter(
                    x=index,
                    y=df[col],
                    name=col,
                    mode="lines",
                ),
                row=i+1,
                col=1,
            )

    if show_trades:
    
        fig.add_trace(
            go.Scatter(
                x=buys,
                y=[df["price"].iloc[i] for i in buys],
                mode="markers",
                name="buy",
                marker=dict(size=5, color="#27AE60"),
                text=[df["trade"].iloc[i] for i in buys],
                hovertext=df["datetime"]
            ),
            row=1,
            col=1,
        )
        
        fig.add_trace(
            go.Scatter(
                x=sells,
                y=[df["price"].iloc[i] for i in sells],
                mode="markers",
                name="sell",
                marker=dict(size=5, color="#E74C3C"),
                text=[df["trade"].iloc[i] for i in sells],
                hovertext=df["datetime"]
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        showlegend=True,
        title=f"Trades",
        margin=go.layout.Margin(l=0, r=0, b=0, t=25),
    ) 
    
    return fig