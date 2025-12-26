import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
import ltgr
import wacc_model # get_wacc_from_financials(ticker, market_ticker,start_date,end_date)
from regression_beta import *
# from financial_extractors import get_effective_tax_rate
global unlevered_beta_median

firms_list = ["TCS.NS","HCLTECH.NS","WIPRO.NS","LTIM.NS","TECHM.NS"] #"INFY.NS",
# firms_list = ["AXISBANK.NS", "KOTAKBANK.NS", "BANKBARODA.NS", "CANBK.NS", "IDFCFIRSTB.NS"] #"HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS",
market_ticker = "^NSEI" # "^NSEBANK" # change this when you chnage firms list
end_date = date.today() # date(2025, 12, 25)
start_date = end_date - relativedelta(years=6)
beta_unlevered_median = main(firms_list, start_date, end_date, market_ticker)

for ticker_str in firms_list:
    ## Pull historical data (Income, Balance Sheet, Cash Flow)
    # ticker_str = "TCS.NS"
    ticker = yf.Ticker(ticker_str)
    firm_name = ticker.info["longName"]
    print("TICKER\t\t\t\t\t :",ticker_str)
    print("firm_name\t\t\t\t :",firm_name)
    print("-------------------------------------------------------------------------------------------------")
    ticker
    ## income statement
    income = ticker.financials.T
    # print(income.columns.tolist())
    # print(income.index)
    ## balance sheet
    balance = ticker.balance_sheet.T
    # print(balance.columns.tolist())
    ## cash flow statement
    cashflow = ticker.cashflow.T
    # print(cashflow.columns.tolist())

    ## Extract key variables
    df = pd.DataFrame(index=income.index)
    df["Revenue"] = income["Total Revenue"]
    df["EBIT"] = income["EBIT"]
    df["Tax"] = income["Tax Provision"]
    df["Depreciation"] = cashflow["Depreciation"]
    df["CapEx"] = cashflow["Capital Expenditure"]
    df["CapEx"] = df["CapEx"].abs()

    # Calculate the change in working capital
    df["Working Capital"] = balance["Working Capital"]
    df['Change in Working Capital'] = balance['Working Capital'].diff(periods=1)

    df = df.dropna() # cleaned negatives

    # historical ratios
    df["Revenue_Growth"] = df["Revenue"].pct_change()
    df["EBIT_Margin"] = df["EBIT"] / df["Revenue"]
    df["CapEx_%_Revenue"] = df["CapEx"] / df["Revenue"]
    df["Dep_%_Revenue"] = df["Depreciation"] / df["Revenue"]
    df["WC_%_Revenue"] = df["Working Capital"] / df["Revenue"]

    # Use medians (robust, professional choice)
    assumptions = {
        "rev_growth": df["Revenue_Growth"].median(),
        "ebit_margin": df["EBIT_Margin"].median(),
        "capex_pct": df["CapEx_%_Revenue"].median(),
        "dep_pct": df["Dep_%_Revenue"].median(),
        "wc_pct": df["WC_%_Revenue"].median(),
        "tax_rate": (df["Tax"] / df["EBIT"]).median()
    }

    # Forecast next 5 years
    forecast_years = 5
    last_revenue = df["Revenue"].iloc[-1]

    forecast = pd.DataFrame(index=range(1, forecast_years+1))

    # Revenue forecast (fade growth)
    growth_rates = np.linspace(
        assumptions["rev_growth"],
        assumptions["rev_growth"] * 0.6,
        forecast_years
    )
    forecast["Revenue"] = last_revenue * (1 + growth_rates).cumprod()

    # operating metrics
    forecast["EBIT"] = forecast["Revenue"] * assumptions["ebit_margin"]
    forecast["Tax"] = forecast["EBIT"] * assumptions["tax_rate"]
    forecast["NOPAT"] = forecast["EBIT"] - forecast["Tax"]
    forecast["Depreciation"] = forecast["Revenue"] * assumptions["dep_pct"]
    forecast["CapEx"] = forecast["Revenue"] * assumptions["capex_pct"]
    forecast["Working Capital"] = forecast["Revenue"] * assumptions["wc_pct"]
    forecast["ΔWC"] = forecast["Working Capital"].diff().fillna(0)

    # compute FCFF
    forecast["FCFF"] = (
        forecast["NOPAT"]
        + forecast["Depreciation"]
        - forecast["CapEx"]
        - forecast["ΔWC"]
    )

    # Discount rafe factor
    risk_free_rate = 0.072
    end_date = date.today() # date(2025, 12, 25)
    start_date = end_date - relativedelta(years=6)
    start_date
    wacc = wacc_model.get_wacc_from_financials(ticker_str, market_ticker, beta_unlevered_median, start_date ,end_date)#["wacc"]
    wacc = wacc["wacc"]

    # terminal value
    terminal_growth = ltgr.get_ltgr(ticker_str)
    fcff_6 = forecast["FCFF"].iloc[-1] * (1 + terminal_growth)
    terminal_value = fcff_6 / (wacc - terminal_growth)
    terminal_value = float(terminal_value.iloc[0])

    # present value of cash flows
    forecast["Discount Factor"] = [(1 / (1 + wacc) ** i) for i in range(1, forecast_years+1)]
    forecast["PV_FCFF"] = forecast["FCFF"] * forecast["Discount Factor"]
    pv_terminal = terminal_value / ((1 + wacc) ** forecast_years)

    # firm value = sum of present value and all FCFFs
    firm_value = forecast["PV_FCFF"].sum() + pv_terminal
    firm_value = float(firm_value.iloc[0])

    # Equity value per share
    cash = float(balance["Cash Cash Equivalents And Short Term Investments"].iloc[-2])
    debt = float(balance["Total Debt"].iloc[-2])
    minority_interest = float(balance["Minority Interest"].iloc[-2])
    net_debt = debt - cash
    shares_outstanding = ticker.info["sharesOutstanding"]
    equity_value = firm_value - debt + cash - minority_interest
    intrinsic_value_per_share = equity_value / shares_outstanding
    current_market_value_per_share = ticker.info["currentPrice"]
    print("intrinsic_value_per_share \t\t :",intrinsic_value_per_share)
    print("current_market_value_per_share \t\t :",current_market_value_per_share)
    if intrinsic_value_per_share < current_market_value_per_share:
        print("Strong recommendation \t\t\t\t : SELL\n\n")
    elif intrinsic_value_per_share > current_market_value_per_share:
        print("Strong recommendation \t\t\t\t : BUY\n\n")
    else:
        print("Strong recommendation \t\t\t\t : HOLD\n\n")
