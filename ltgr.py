"""
NOPAT = EBIT (1 - tax rate)
Invested Capital = Net Fixed Assets + Working Capital
Reinvestment= Capex - Depreciation + ΔWC
ROIC = NOPAT / Invested Capital
Reinvestment Rate = Reinvestment​ / NOPAT
ltgr = ROIC * Reinvestment Rate
"""
import yfinance as yf
import pandas as pd
import numpy as np

"""
ROIC (average) — how efficiently the company turns capital into profit
Reinvestment Rate (average) — how much of NOPAT is plowed back
Implied Long-Term g — economically justified growth
Terminal g — caps growth at a realistic ceiling (default 6%)
"""

def compute_total_current_assets(balance_df):
    current_asset_fields = [
        "Cash And Cash Equivalents",
        "Cash Equivalents",
        "Cash Financial",
        "Other Short Term Investments",
        "Accounts Receivable",
        "Inventory",
        "Prepaid Assets",
        "Other Current Assets",
        "Restricted Cash",
        "Taxes Receivable",
        "Other Receivables"
    ]
    existing_fields = [c for c in current_asset_fields if c in balance_df.columns]
    if not existing_fields:
        raise ValueError("No current asset fields found in balance sheet")
    total_current_assets = balance_df[existing_fields].sum(axis=1)
    return total_current_assets

def compute_total_current_liabilities(balance_df):
    current_liability_fields = [
        "Accounts Payable",
        "Payables",
        "Other Payable",
        "Dividends Payable",
        "Total Tax Payable",
        "Current Provisions",
        "Other Current Liabilities",
        "Current Debt And Capital Lease Obligation",
        "Current Capital Lease Obligation",
        "Pensionand Other Post Retirement Benefit Plans Current"
    ]
    existing_fields = [c for c in current_liability_fields if c in balance_df.columns]
    if not existing_fields:
        raise ValueError("No current liability fields found in balance sheet")
    total_current_liabilities = balance_df[existing_fields].sum(axis=1)
    return total_current_liabilities

def get_ltgr(ticker):

    def fetch_financials(ticker):
        stock = yf.Ticker(ticker)

        # Get annual statements
        income = stock.financials.T
        balance = stock.balance_sheet.T
        cashflow = stock.cashflow.T

        return income, balance, cashflow

    def compute_growth_rate(ticker):
        inc, bal, cf = fetch_financials(ticker)

        # Ensure year index
        inc.index = inc.index.year
        bal.index = bal.index.year
        cf.index = cf.index.year

        # Align years
        years = sorted(list(set(inc.index) & set(bal.index) & set(cf.index)))
        inc = inc.loc[years]
        bal = bal.loc[years]
        cf = cf.loc[years]

        # Compute NOPAT
        ebit = inc["Ebit"] if "Ebit" in inc else inc["EBIT"]
        tax_rate = 0.30  # placeholder if no tax data
        nopat = ebit * (1 - tax_rate)

        # Compute Total current assets, Total Current Liabilities
        bal["Total Current Assets"] = compute_total_current_assets(bal)
        bal["Total Current Liabilities"] = compute_total_current_liabilities(bal)
        assert bal["Total Current Assets"].isna().sum() == 0 # sanity checks
        assert bal["Total Current Liabilities"].isna().sum() == 0 # sanity checks
        
        # Invested Capital = Net PPE + Working Capital
        net_ppe = bal["Property Plant Equipment Net"] if "Property Plant Equipment Net" in bal else bal["Net PPE"]
        working_capital = (bal["Total Current Assets"] - bal["Total Current Liabilities"])

        invested_capital = net_ppe + working_capital
        assert invested_capital.min() > 0

        # Compute ROIC
        roic = nopat / invested_capital.replace(0, np.nan)

        # Reinvestment = Capex + ΔWC - Depreciation
        capex = cf["Capital Expenditure"]
        depreciation = cf["Depreciation"]
        delta_wc = working_capital.diff()

        reinvestment = capex + delta_wc - depreciation

        # Reinvestment Rate
        reinvest_rate = reinvestment / nopat.replace(0, np.nan)

        # Compute g
        g = roic * reinvest_rate

        # Clean
        roic_clean = roic.dropna()
        reinvest_clean = reinvest_rate.dropna()
        g_clean = g.dropna()

        return roic_clean, reinvest_clean, g_clean

    def get_terminal_growth(ticker, g_ceiling=0.06):
        roic, reinvest_rate, g = compute_growth_rate(ticker)

        long_term_roic = roic.mean()
        long_term_reinvest = reinvest_rate.mean()
        long_term_g = g.mean()

        terminal_g = min(long_term_g, g_ceiling)

        results = {
            "ROIC [Return over Investment Capital] (%)": long_term_roic * 100,
            "Reinvestment Rate (%)                    ": long_term_reinvest * 100,
            "Implied Growth [LTGR] (g %)              ": long_term_g * 100,
            "Terminal Growth (g %)                    ": terminal_g * 100
        }
        for k, v in results.items():
            print(f"{k}: {v:.2f}%")
        return float(long_term_g*100)
    
    ltgr_returned = get_terminal_growth(ticker)
    return(ltgr_returned)

# if __name__ == "__main__":
#     ticker = "TCS.NS"
#     results = get_terminal_growth(ticker)
#     print(f"Growth Summary for {ticker}:")
# for k, v in results.items():
#     print(f"{k}: {v:.2f}%")

# ltgr("TMCV.NS")