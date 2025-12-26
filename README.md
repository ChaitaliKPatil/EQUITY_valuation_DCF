# EQUITY_valuation_DCF
Recommending buy, sell or hold utilizing yfinance to perform automated sector peer comparisons amongst industry competitors. The system streamlines investment decision-making by delivering precise book value valuations and actionable buy/sell/hold recommendations based on real-time competitive market data and regressions.

1. I have collected the company financials and documents using the open source python library called "yfinance" to evaluate the model with the yfinance restrictions of historical data availability upto maximum of 4-5 years.

2. Calculationg the WACC, for each company in the competitors list to find the discounting value factor to get the present valuations of the future cash flows to the firm in next 4 to 5 years.

3. Relevering of beta is necessary to avoid large std.deviation errors and hence covariance/variance is preferred initially and the normalization with the help of medians in order to fit into the industry classification terms.

4. Terminal value reflects the value of firm in infinite time period where the long term growth rate comes into play. Knowing the present value of terminal value is importnt to get the valuations of cash flows in todays's date.

5. firm value = sum pf PV of FCFF + PV of terminal value

6. In order to get the equity valuation per share, we have to consider various factors such as debt, cash, investments, interests.

7. Various statistical calculations are performed along with regressions.
