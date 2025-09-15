import pandas as pd
import numpy as np

def calculate_return(df, days):
    if len(df) < days:
        return 0
    start = df["nav"].iloc[-days]
    end = df["nav"].iloc[-1]
    return round((end - start) / start * 100, 2)

def calculate_volatility(df, days):
    if len(df) < days:
        return 0
    returns = df["nav"].pct_change().tail(days)
    return round(returns.std() * (252 ** 0.5) * 100, 2)

def calculate_sharpe(df, days, risk_free_rate=0.05):
    if len(df) < days:
        return 0
    returns = df["nav"].pct_change().tail(days)
    avg_return = returns.mean() * 252
    vol = returns.std() * (252 ** 0.5)
    if vol == 0:
        return 0
    return round((avg_return - risk_free_rate) / vol, 2)
