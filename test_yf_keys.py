import yfinance as yf
n = yf.Ticker("AAPL").news
if n:
    print(n[0])
else:
    print("No news found")
