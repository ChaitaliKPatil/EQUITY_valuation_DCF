# beta_engine.py

import yfinance as yf
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statistics


def compute_levered_beta(stock, market, start_date, end_date, freq="ME"):

    stock_px = yf.download(stock, start_date, end_date, progress=False)["Close"]
    market_px = yf.download(market, start_date, end_date, progress=False)["Close"]

    stock_px = stock_px.resample(freq).last()
    market_px = market_px.resample(freq).last()

    stock_ret = np.log(stock_px / stock_px.shift(1))
    market_ret = np.log(market_px / market_px.shift(1))

    df = pd.concat([stock_ret, market_ret], axis=1).dropna()
    df.columns = ["stock", "market"]

    X = sm.add_constant(df["market"])
    y = df["stock"]

    return sm.OLS(y, X).fit().params["market"]

def unlevered_beta(ticker, start_date, end_date, market_ticker="^NSEI", years=6):
    prices = yf.download(ticker, start_date, end_date, progress=False)["Close"] # auto_adjust=True as default
    shares = yf.Ticker(ticker).info.get("sharesOutstanding")
    market_cap_series = prices * shares
    bs = yf.Ticker(ticker).balance_sheet
    fin = yf.Ticker(ticker).financials
    tax = fin.loc["Tax Provision"].iloc[:years]
    pretax = fin.loc["Pretax Income"].iloc[:years]
    rate = (tax / pretax).replace([np.inf, -np.inf], np.nan).dropna()
    tax_rate = rate.mean()
    de_ratio = bs.loc["Total Debt"].iloc[:years].mean() / market_cap_series.mean()
    beta_levered = compute_levered_beta(ticker, market_ticker, start_date, end_date)
    beta_unlevered = beta_levered / (1 + (1 - tax_rate) * de_ratio)
    # print(float(beta_unlevered.iloc[0]))
    return float(beta_unlevered.iloc[0])

def main(firms_list, start_date, end_date, market_ticker):
    ul_beta_list = [unlevered_beta(f, start_date, end_date, market_ticker) for f in firms_list]
    ul_beta = statistics.median(ul_beta_list)
    return ul_beta
#     ticker = "TCS.NS"
#     results = get_terminal_growth(ticker)
#     print(f"Growth Summary for {ticker}:")
# for k, v in results.items():
#     print(f"{k}: {v:.2f}%")
