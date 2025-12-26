"""
Download stock & market prices
Compute levered beta (regression)
Unlever beta (remove capital structure)
Relever beta (target capital structure)
Compute cost of equity
Compute cost of debt
Compute WACC
"""
from regression_beta import *


def get_wacc_from_financials(ticker_str, market_ticker, beta_unlevered_median, start_date="01-01-2020", end_date="25-12-2025", risk_free_rate=0.072):

    ticker = ticker_str
    market_ticker = market_ticker
    start_date = start_date
    end_date = end_date

    def get_average_market_cap(ticker, start_date, end_date):
        prices = yf.download(ticker, start_date, end_date, progress=False)["Close"] # auto_adjust=True as default
        shares = yf.Ticker(ticker).info.get("sharesOutstanding")
        market_cap_series = prices * shares
        return market_cap_series.mean()


    def get_average_total_debt(ticker, years=3):
        bs = yf.Ticker(ticker).balance_sheet
        return bs.loc["Total Debt"].iloc[:years].mean()


    def get_effective_tax_rate(ticker, years=3):
        fin = yf.Ticker(ticker).financials
        tax = fin.loc["Tax Provision"].iloc[:years]
        pretax = fin.loc["Pretax Income"].iloc[:years]
        rate = (tax / pretax).replace([np.inf, -np.inf], np.nan).dropna()
        return rate.mean()


    def get_cost_of_debt(ticker, years=3):
        fin = yf.Ticker(ticker).financials
        bs = yf.Ticker(ticker).balance_sheet
        interest = fin.loc["Interest Expense"].iloc[:years].abs().mean()
        debt = bs.loc["Total Debt"].iloc[:years].mean()
        return interest / debt


    def get_equity_risk_premium(market_ticker, beta_unlevered_median, start_date, end_date, risk_free_rate, freq="ME"):
        """
        Computes realized ERP from market index returns.

        ERP (India) ≈ CAGR of NIFTY Total Return − Rf
        """

        prices = yf.download(
            market_ticker,
            start_date,
            end_date,
            progress=False
        )["Close"] #auto_adjust=True by default

        prices = prices.resample(freq).last()

        returns = np.log(prices / prices.shift(1)).dropna()

        market_return = returns.mean() * 12  # annualized
        erp = market_return - risk_free_rate

        return erp

    # --- Financials (Capital structure averaged)---
    E = get_average_market_cap(ticker, start_date, end_date)
    D = get_average_total_debt(ticker, years=3)
    
    de_ratio = D / E

    # --- tax and debt cost ---
    tax_rate = get_effective_tax_rate(ticker, years=3)
    Rd_pre_tax = get_cost_of_debt(ticker, years=3)

    # --- market risk ---
    equity_risk_premium = get_equity_risk_premium(market_ticker, beta_unlevered_median, start_date, end_date, risk_free_rate)

    # --- Beta ---
    beta_levered = compute_levered_beta(ticker, market_ticker, start_date, end_date)

    beta_unlevered = beta_levered / (1 + (1 - tax_rate) * de_ratio)
    beta_relevered = beta_unlevered_median * (1 + (1 - tax_rate) * de_ratio)

    # --- Costs ---
    print("\nrisk_free_rate\t\t\t\t :",f"{risk_free_rate*100:.2f}%","\nbeta_relevered\t\t\t\t :",f"{beta_relevered.iloc[0]:.2f}","\nequity_risk_premium\t\t\t :",f"{equity_risk_premium.iloc[0]*100:.2f}%")
    beta_relevered = float(beta_relevered.iloc[0])
    equity_risk_premium = float(equity_risk_premium.iloc[0])
    cost_of_equity = risk_free_rate + beta_relevered * equity_risk_premium
    cost_of_debt_after_tax = Rd_pre_tax * (1 - tax_rate)

    # --- Weights ---
    w_e = E / (E + D)
    w_d = D / (E + D)

    # --- WACC ---
    wacc = w_e * cost_of_equity + w_d * cost_of_debt_after_tax

    return {
        "equity_risk_premium": equity_risk_premium,
        "levered_beta": beta_levered,
        "relevered_beta": beta_relevered,
        "cost_of_equity": cost_of_equity,
        "cost_of_debt_after_tax": cost_of_debt_after_tax,
        "equity_weight": w_e,
        "debt_weight": w_d,
        "tax_rate": tax_rate,
        "wacc": wacc
    }

