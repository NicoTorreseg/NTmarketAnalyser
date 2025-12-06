import requests
import yfinance as yf
import pandas as pd
from typing import List
from config import (
    CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS, WATCHLIST_MERVAL,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY,
    TV_HEADERS, TV_COOKIES, TV_COLUMNS, TV_RAW_LISTS,
    TV_COIN_URL, TV_COIN_COLUMNS # <--- IMPORTANTE: Nuevas variables
)
from GoogleNews import GoogleNews
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)

class NewsIntel:
    def __init__(self):
        self.googlenews = GoogleNews(lang='en', period='1d') # Noticias de últimas 24h
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def get_sentiment_analysis(self, symbol: str, asset_name: str = "", is_crypto: bool = True, is_merval: bool = False) -> dict:
        """
        Busca noticias con contexto dinámico de idioma y región.
        """
        # 1. AJUSTE DE IDIOMA SEGÚN MERCADO 🔥
        if is_merval:
            # Si es Merval, forzamos Español y región Argentina
            self.googlenews = GoogleNews(lang='es', region='AR')
            # Limpiamos el nombre (a veces viene como "Grupo Financiero Galicia S.A.")
            clean_name = asset_name.split(' inc')[0].split(' S.A.')[0].split(' Corp')[0]
            # Búsqueda más natural para diarios argentinos
            search_term = f"{clean_name} acciones economía"
        else:
            # Para Crypto y Stocks USA, seguimos en Inglés
            self.googlenews = GoogleNews(lang='en') 
            if is_crypto:
                search_term = f"{asset_name} cryptocurrency" if asset_name else f"{symbol} crypto coin"
            else:
                search_term = f"{symbol} stock news"

        print(f"🧠 [IA] Buscando ({'ES' if is_merval else 'EN'}): '{search_term}'...")
        
        # 2. EJECUCIÓN (Igual que antes)
        self.googlenews.clear()
        self.googlenews.search(search_term)
        results = self.googlenews.result()
        
        # Reintento inteligente para Merval
        if not results and is_merval:
             print(f"   ⚠️ Reintentando con ticker: {symbol}...")
             self.googlenews.search(f"{symbol} acciones merval")
             results = self.googlenews.result()

        if not results:
            return {"score": 50, "decision": "NEUTRAL", "reason": f"Sin noticias para {search_term}"}

        # 3. PROMPT CONTEXTUALIZADO (Ajustamos el rol de la IA)
        top_news = [f"- {item['title']} (Source: {item['media']})" for item in results[:5]]
        news_text = "\n".join(top_news)

        if is_crypto:
            asset_type = "cryptocurrency"
            role = "Crypto Analyst, Senior Financial Analyst "
        elif is_merval:
            asset_type = "Argentine Stock, "
            # 🔥 Le decimos a la IA que piense como experto en Latam
            role = "Senior Financial Analyst in Emerging Markets and Argentina (Merval)" 
        else:
            asset_type = "stock"
            role = "Senior Financial Analyst Wall Street Expert"
        
        prompt = f"""
        Role: {role}.
        Asset: {asset_name if asset_name else symbol} ({asset_type}).
        Ticker: {symbol}
        
        Recent Headlines:
        {news_text}

        Task: 
        1. Analyze sentiment considering local economic context (inflation, regulations).
        2. Filter out irrelevant news (e.g., if analyzing 'Dash' crypto, ignore 'DoorDash' stocks).
        3. Identify FUD, Hype, or Fundamentals.
        4. Analyze the sentiment ONLY based on relevant news.

        Response format (JSON only):
        {{
            "score": (integer 0-100, 0=Panic, 50=Neutral/Irrelevant, 100=Greed),
            "decision": ("BUY", "WAIT", "NEUTRAL"),
            "reason": "Brief explanation in Spanish. If news are irrelevant, state it."
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            import json
            analysis = json.loads(clean_json)
            return analysis
        except Exception as e:
            print(f"❌ Error IA: {e}")
            return {"score": 50, "decision": "ERROR", "reason": "Fallo en IA"}

# --- CLASE NOTIFICADOR ---
class Notifier:
    """Encargada de enviar alertas a Telegram."""
    
    @staticmethod
    def send_telegram_alert(message: str):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Faltan credenciales de Telegram en config.py")
            return

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

# --- CLASE ANALISTA DE MERCADO ---
class MarketAnalyzer:
    def __init__(self):
        self.api_key = CMC_API_KEY
        # Usamos cmc_headers para estandarizar el acceso a CoinMarketCap
        self.cmc_headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }
        # Mantenemos self.headers por compatibilidad si algo lo usa, pero apuntando a lo mismo
        self.headers = self.cmc_headers


    # --- 3. SCANNER DE CRYPTO COINS (NUEVO) ---
    # --- 3. SCANNER DE CRYPTO COINS (Lógica de tradingview.py) ---
    def scan_coin_market(self, limit=300):
        """
        Escanea el mercado Cripto. (Listas definidas internamente para evitar NameErrors).
        """
        # 1. Definimos las listas AQUÍ DENTRO para que la función sea autónoma
        local_lists = [
            ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","close","pricescale","minmov","fractional","minmove2","currency","24h_close_change|5","market_cap_calc","fundamental_currency_code","24h_vol_cmc","circulating_supply","24h_vol_to_market_cap","socialdominance","crypto_common_categories.tr","TechRating_1D","TechRating_1D.tr"],
            ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","market_cap_calc","fundamental_currency_code","24h_close_change|5","Perf.W","Perf.1M","Perf.3M","Perf.6M","Perf.YTD","Perf.Y","Perf.5Y","Perf.10Y","Perf.All","Volatility.D"],
            ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","TechRating_1D","TechRating_1D.tr","MARating_1D","MARating_1D.tr","OsRating_1D","OsRating_1D.tr","RSI","Mom","pricescale","minmov","fractional","minmove2","AO","CCI20","Stoch.K","Stoch.D","Candle.3BlackCrows","Candle.3WhiteSoldiers","Candle.AbandonedBaby.Bearish","Candle.AbandonedBaby.Bullish","Candle.Doji","Candle.Doji.Dragonfly","Candle.Doji.Gravestone","Candle.Engulfing.Bearish","Candle.Engulfing.Bullish","Candle.EveningStar","Candle.Hammer","Candle.HangingMan","Candle.Harami.Bearish","Candle.Harami.Bullish","Candle.InvertedHammer","Candle.Kicking.Bearish","Candle.Kicking.Bullish","Candle.LongShadow.Lower","Candle.LongShadow.Upper","Candle.Marubozu.Black","Candle.Marubozu.White","Candle.MorningStar","Candle.ShootingStar","Candle.SpinningTop.Black","Candle.SpinningTop.White","Candle.TriStar.Bearish","Candle.TriStar.Bullish"]
        ]

        # 2. Aplanar la lista manteniendo el orden (Vitales primero)
        final_columns_list = []
        seen = set()
        for sublist in local_lists:
            for item in sublist:
                if item not in seen:
                    seen.add(item)
                    final_columns_list.append(item)

        payload = {
            "columns": final_columns_list,
            "ignore_unknown_fields": False, 
            "options": {"lang": "es"},
            "range": [0, limit], 
            "sort": {"sortBy": "crypto_total_rank", "sortOrder": "asc"},
            "symbols": {}, 
            "markets": ["coin"]
        }
        
        try:
            r = requests.post(TV_COIN_URL, headers=TV_HEADERS, cookies=TV_COOKIES, json=payload, timeout=10)
            
            if r.status_code == 200:
                json_data = r.json()
                if 'data' in json_data:
                    df = pd.DataFrame([d['d'] for d in json_data['data']])
                    
                    # Asignación segura de columnas
                    cols_to_assign = final_columns_list
                    if len(df.columns) < len(final_columns_list):
                        cols_to_assign = final_columns_list[:len(df.columns)]
                    
                    df.columns = cols_to_assign
                    return df
            else:
                print(f"❌ Crypto TV HTTP Error: {r.status_code}")

        except Exception as e: 
            print(f"❌ Crypto TV Exception: {e}")
            
        return pd.DataFrame()

    # =========================================================================
    # 2. FUNCIÓN DE PROCESAMIENTO (Igual a procesar_crypto_tecnico)
    # =========================================================================
    def _process_crypto_technicals(self, df_raw):
        """
        Toma el DF crudo, renombra la columna de cambio y genera el string de patrones.
        """
        if df_raw.empty: return df_raw

        df = df_raw.copy()

        # 1. Renombrar columna de cambio (La famosa |5)
        # La buscamos con exactitud o variantes comunes
        col_rara = "24h_close_change|5"
        if col_rara in df.columns:
            df.rename(columns={col_rara: "change"}, inplace=True)
        
        # Asegurar que sea float
        if "change" in df.columns:
            df["change"] = pd.to_numeric(df["change"], errors='coerce').fillna(0.0)

        # 2. Detectar Patrones de Velas
        candle_cols = [c for c in df.columns if "Candle." in c]
        
        def detectar(row):
            patrones = []
            for col in candle_cols:
                if pd.notna(row[col]) and row[col] == 1:
                    nombre = col.replace("Candle.", "").replace(".", " ")
                    patrones.append(nombre)
            return ", ".join(patrones) if patrones else None # Retorna None si no hay, para limpieza

        if candle_cols:
            df['Patrones_Hoy'] = df.apply(detectar, axis=1)
        else:
            df['Patrones_Hoy'] = None

        return df
    # --- MÉTODOS DE BÚSQUEDA ---

    # --- 1. MOTOR DE TRADINGVIEW (CORE) ---
    def scan_tradingview(self, markets=None, limit=500):
        """Obtiene el DataFrame crudo de TradingView (Precios + Técnicos)."""
        url = 'https://scanner.tradingview.com/global/scan'
        target_markets = markets if markets else ["america", "argentina", "brazil", "mexico"]
        
        payload = {
            "columns": TV_COLUMNS,
            "ignore_unknown_fields": False,
            "options": {"lang": "es"},
            "range": [0, limit],
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "symbols": {},
            "markets": target_markets,
            "filter2": {
                "operator": "and",
                "operands": [
                    {
                        "operation": {
                            "operator": "or",
                            "operands": [
                                {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "stock"}}, {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}]}},
                                {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "stock"}}, {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}]}},
                                {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "dr"}}]}}
                            ]
                        }
                    },
                    {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["pre-ipo"]}}
                ]
            }
        }

        try:
            response = requests.post(url, headers=TV_HEADERS, cookies=TV_COOKIES, json=payload, timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if 'data' in json_data:
                    df = pd.DataFrame([d['d'] for d in json_data['data']])
                    if len(df.columns) == len(TV_COLUMNS):
                        df.columns = TV_COLUMNS
                    return df
        except Exception as e:
            print(f"❌ Error Scanner TradingView: {e}")
        return pd.DataFrame()

    # --- 2. PROCESADOR DE DATOS TÉCNICOS ---
    def _process_technicals(self, df_completo):
        """
        Limpia el DataFrame crudo y traduce las velas (0/1) a texto legible.
        Equivale a tu función 'generar_dataframe_tecnico'
        """
        if df_completo.empty: return pd.DataFrame()

        # Lista 3 (Técnicos) + Contexto
        columnas_deseadas = TV_RAW_LISTS[2] + ['close', 'change', 'volume', 'description']
        cols_existentes = list(set(c for c in columnas_deseadas if c in df_completo.columns))
        df_tech = df_completo[cols_existentes].copy()

        # Detectar Patrones de Velas
        candle_cols = [c for c in df_tech.columns if "Candle." in c]
        
        def detectar(row):
            encontrados = []
            for col in candle_cols:
                if pd.notna(row[col]) and row[col] == 1:
                    nombre = col.replace("Candle.", "").replace(".", " ")
                    encontrados.append(nombre)
            return ", ".join(encontrados) if encontrados else None

        if candle_cols:
            df_tech['Patrones_Hoy'] = df_tech.apply(detectar, axis=1)
        else:
            df_tech['Patrones_Hoy'] = None
            
        return df_tech
    
    
    

    def get_current_price(self, symbol: str) -> float:
        """
        Intenta obtener el precio de 3 fuentes en orden:
        1. Yahoo Finance (Stocks/Cripto)
        2. Binance (Cripto API Pública)
        3. CoinMarketCap (Tu API Key - Último recurso)
        """
        # --- A. INTENTO YAHOO FINANCE ---
        try:
            ticker_str = symbol if symbol in WATCHLIST_STOCKS or symbol in WATCHLIST_MERVAL else f"{symbol}-USD"
            ticker = yf.Ticker(ticker_str)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return hist['Close'].iloc[-1]
        except Exception:
            pass # Falló Yahoo, seguimos...

        # --- B. INTENTO BINANCE (Solo Criptos) ---
        if symbol not in WATCHLIST_STOCKS or symbol not in WATCHLIST_MERVAL:
            try:
                # Binance usa pares sin guion, ej: BTCUSDT
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    price = float(data['price'])
                    print(f"✅ Precio {symbol} obtenido de Binance: {price}")
                    return price
            except Exception:
                pass # Falló Binance, seguimos...

        # --- C. INTENTO COINMARKETCAP (Fuente de Verdad) ---
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}
            r = requests.get(url, headers=self.cmc_headers, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                price = data['data'][symbol]['quote']['USD']['price']
                print(f"✅ Precio {symbol} obtenido de CoinMarketCap: {price}")
                return price
        except Exception as e:
            print(f"❌ Fallaron todas las fuentes para {symbol}: {e}")
        
        return 0.0

    # --- MÉTODO EN CASCADA (FIX PARA COMPRAS) ---
    # def get_current_price(self, symbol: str) -> float:
    #     """
    #     Intenta obtener el precio de 3 fuentes en orden:
    #     1. Yahoo Finance (Stocks/Cripto)
    #     2. Binance (Cripto API Pública)
    #     3. CoinMarketCap (Tu API Key - Último recurso)
    #     """
    #     # --- A. INTENTO YAHOO FINANCE ---
    #     try:
    #         ticker_str = symbol if symbol in WATCHLIST_STOCKS or symbol in WATCHLIST_MERVAL else f"{symbol}-USD"
    #         ticker = yf.Ticker(ticker_str)
    #         hist = ticker.history(period="1d")
    #         if not hist.empty:
    #             return hist['Close'].iloc[-1]
    #         else:
    #             price = ticker.fast_info.last_price
    #             if price: return price 
    #             else: 
    #                 print("No price data in Yahoo finance.")

    #     except Exception:
    #         pass # Falló Yahoo, seguimos...

    #     # --- B. INTENTO BINANCE (Solo Criptos) ---
    #     if symbol not in WATCHLIST_STOCKS or symbol not in WATCHLIST_MERVAL:
    #         try:
    #             # Binance usa pares sin guion, ej: BTCUSDT
    #             url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    #             r = requests.get(url, timeout=3)
    #             if r.status_code == 200:
    #                 data = r.json()
    #                 price = float(data['price'])
    #                 print(f"✅ Precio {symbol} obtenido de Binance: {price}")
    #                 return price
    #         except Exception:
    #             pass # Falló Binance, seguimos...

    #     # --- C. INTENTO COINMARKETCAP (Fuente de Verdad) ---
    #     try:
    #         url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    #         params = {'symbol': symbol, 'convert': 'USD'}
    #         r = requests.get(url, headers=self.cmc_headers, params=params, timeout=5)
    #         if r.status_code == 200:
    #             data = r.json()
    #             price = data['data'][symbol]['quote']['USD']['price']
    #             print(f"✅ Precio {symbol} obtenido de CoinMarketCap: {price}")
    #             return price
    #     except Exception as e:
    #         print(f"❌ Fallaron todas las fuentes para {symbol}: {e}")
        
    #     return 0.0

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        if len(series) < period + 1: return 50.0
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        if float(loss.iloc[-1]) == 0: return 100.0
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)

    def get_market_sentiment(self):
        try:
            url = "https://api.alternative.me/fng/"
            r = requests.get(url, timeout=3)
            data = r.json()
            return data['data'][0] 
        except Exception:
            return {"value": "Unknown", "classification": "Error"}

    def get_market_data(self):
        if USE_MOCK_DATA: return self._get_mock_data()
        parameters = {'start': '1', 'limit': '100', 'convert': 'USD'}
        try:
            response = requests.get(CMC_BASE_URL, headers=self.cmc_headers, params=parameters)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Error CoinMarketCap: {e}")
            return []

    def find_market_opportunities(self, market_type: str, threshold: float) -> List[dict]:
        """
        Escáner Universal: Sirve para Crypto, USA y Merval.
        market_type: 'CRYPTO', 'USA', 'MERVAL'
        """
        print(f"📡 Escaneando {market_type} (Threshold: {threshold}%)...")
        
        # 1. ELEGIR FUENTE DE DATOS
        if market_type == 'CRYPTO':
            df_raw = self.scan_coin_market(limit=300)
            df = self._process_crypto_technicals(df_raw)
            col_change = 'change' # En tu código crypto ya lo renombraste a 'change'
            min_vol = 0 # Opcional
        elif market_type == 'USA':
            df_raw = self.scan_tradingview(markets=["america"], limit=800)
            df = self._process_technicals(df_raw)
            col_change = 'change'
            min_vol = 50000 # Filtro de volumen para USA
        elif market_type == 'MERVAL':
            df_raw = self.scan_tradingview(markets=["argentina"], limit=400)
            df = self._process_technicals(df_raw)
            col_change = 'change'
            min_vol = 0

        if df.empty: return []

        # 2. FILTRADO COMÚN
        # Filtramos por caída y volumen (si aplica)
        mask = (df[col_change] <= threshold)
        if min_vol > 0 and 'volume' in df.columns:
            mask = mask & (df['volume'] > min_vol)
            
        filtered = df[mask].copy() # Importante usar .copy() para evitar warnings

    # 🔥 NUEVO: FILTRO ANTI-REPETIDOS 🔥
    # Si tenemos la columna 'description' (Nombre de la empresa), borramos duplicados.
    # keep='first' significa que se queda con el primero que aparece y borra los demás.
        if 'description' in filtered.columns:
            # 1. Función lambda para limpiar "basura" financiera
            def clean_name(text):
                if not isinstance(text, str): return str(text)
                text = text.upper()
                # Lista de palabras 'ruido' que hacen que los nombres parezcan distintos
                noise_words = [
                    " CEDEAR", " ADR", " S.A.", " SA", " INC.", " INC", " CORP", " LTD", 
                    " PLC", " AG", " SHS", " CERT DEPOSITO", " ARG REPR", " SP ADR"
                ]
                for word in noise_words:
                    text = text.replace(word, "")
                # Truco extra: Quedarse solo con las primeras 2 palabras suele bastar
                # para diferenciar "Coca Cola" de "Banco Galicia"
                return " ".join(text.split()[:2])

            # 2. Creamos columna temporal 'clean_id'
            filtered['clean_id'] = filtered['description'].apply(clean_name)
            
            len_antes = len(filtered)
            # 3. Borramos duplicados basándonos en el nombre LIMPIO
            filtered = filtered.drop_duplicates(subset=['clean_id'], keep='first')
            
            print(f"   ✂️ Deduplicación Agresiva: {len_antes} -> {len(filtered)} (Se borraron {len_antes - len(filtered)} repetidos).")

        opportunities = []

        # 3. UNIFICACIÓN DE FORMATO
        for _, row in filtered.iterrows():
            # Lógica de RSI y Velas (Idéntica para todos)
            rsi = row.get('RSI', 50)
            patron = row.get('Patrones_Hoy')
            
            tech_msg = []
            if patron: tech_msg.append(f"🕯️ {patron}")
            if rsi < 30: tech_msg.append(f"💎 Oversold ({round(rsi)})")
            
            signal_reason = " | ".join(tech_msg) if tech_msg else "Dip detected"
            
            # Detectar nombre y símbolo según el mercado
            symbol = row.get('base_currency', row.get('name'))
            name = row.get('base_currency_desc', row.get('description', symbol))

            opportunities.append({
                "symbol": symbol,
                "name": name,
                "price": float(row['close']),
                "percent_change": float(row[col_change]), # Unificamos nombre del campo
                "rsi": float(rsi) if pd.notna(rsi) else 50,
                "technical_signal": signal_reason,
                # Datos vacíos de IA para llenar después
                "ai_score": None, "ai_decision": None, "ai_reason": None
            })

        opportunities.sort(key=lambda x: x['percent_change'])
        return opportunities[:20]
    

    
    
    # def find_stock_dips(self, threshold: float = -3.0) -> List[dict]:
    #     opportunities = []
    #     try:
    #         tickers = yf.Tickers(" ".join(WATCHLIST_STOCKS))
    #         for symbol in WATCHLIST_STOCKS:
    #             try:
    #                 ticker = tickers.tickers[symbol]
    #                 hist = ticker.history(period="1mo")
    #                 if len(hist) >= 15:
    #                     current = hist['Close'].iloc[-1]
    #                     prev = hist['Close'].iloc[-2]
    #                     change_pct = ((current - prev) / prev) * 100
    #                     rsi_val = self._calculate_rsi(hist['Close'])
    #                     if change_pct <= threshold:
    #                         opportunities.append({
    #                             "symbol": symbol, "price": round(current, 2),
    #                             "percent_change": round(change_pct, 2), "rsi": rsi_val
    #                         })
    #             except Exception:
    #                 continue
    #     except Exception:
    #         pass
    #     opportunities.sort(key=lambda x: x['percent_change'])
    #     return opportunities
    
    # def find_merval_dips(self, threshold: float = -2.0) -> List[dict]:
    #     """Escanea ADRs Argentinos en Wall Street."""
    #     opportunities = []
    #     try:
    #         tickers = yf.Tickers(" ".join(WATCHLIST_MERVAL))
    #         for symbol in WATCHLIST_MERVAL:
    #             try:
    #                 ticker = tickers.tickers[symbol]
    #                 hist = ticker.history(period="1mo")
    #                 if len(hist) >= 15:
    #                     current = hist['Close'].iloc[-1]
    #                     prev = hist['Close'].iloc[-2]
    #                     change_pct = ((current - prev) / prev) * 100
    #                     rsi_val = self._calculate_rsi(hist['Close'])
                        
    #                     if change_pct <= threshold:
    #                         opportunities.append({
    #                             "symbol": symbol, "price": round(current, 2), 
    #                             "percent_change": round(change_pct, 2), "rsi": rsi_val
    #                         })
    #             except Exception:
    #                 continue
    #     except Exception:
    #         pass
    #     opportunities.sort(key=lambda x: x['percent_change'])
    #     return opportunities
    
    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
        ]