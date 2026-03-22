from GoogleNews import GoogleNews

def test_queries():
    print("Testing EN...")
    gn_en = GoogleNews(lang='en', period='3d')
    test_cases_usa = [
        "AAPL stock news",
        "AAPL stock",
        "Apple stock",
        "Nvidia",
        "NVDA stock"
    ]
    for q in test_cases_usa:
        gn_en.clear()
        gn_en.search(q)
        res = gn_en.result()
        print(f"USA [{q}]: {len(res)} results")
        if res:
             print(f"  Sample: {res[0]['title']}")

    print("\nTesting ES (MERVAL)...")
    gn_es = GoogleNews(lang='es', region='AR', period='3d')
    test_cases_arg = [
        "Galicia acciones economía",
        "Galicia acciones",
        "GGAL merval",
        "YPF acciones",
        "MercadoLibre acciones"
    ]
    for q in test_cases_arg:
        gn_es.clear()
        gn_es.search(q)
        res = gn_es.result()
        print(f"ARG [{q}]: {len(res)} results")
        if res:
             print(f"  Sample: {res[0]['title']}")

if __name__ == "__main__":
    test_queries()
