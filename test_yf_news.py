import yfinance as yf

def test_yf():
    print("Testing AAPL (USA):")
    aapl = yf.Ticker("AAPL")
    for n in aapl.news[:3]:
        print("  -", n.get('title', ''))
        
    print("\nTesting GGAL.BA (MERVAL):")
    ggal = yf.Ticker("GGAL.BA")
    for n in ggal.news[:3]:
         print("  -", n.get('title', ''))
         
    print("\nTesting BTC-USD (CRYPTO):")
    btc = yf.Ticker("BTC-USD")
    for n in btc.news[:3]:
         print("  -", n.get('title', ''))

if __name__ == "__main__":
    test_yf()
