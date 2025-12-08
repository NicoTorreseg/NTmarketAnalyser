import requests
import yfinance as yf
import pandas as pd
from typing import List
from config import (
    CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS, WATCHLIST_MERVAL,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY, GROQ_API_KEY,
    TV_HEADERS, TV_COOKIES, TV_COLUMNS, TV_RAW_LISTS,
    TV_COIN_URL, TV_COIN_COLUMNS # <--- IMPORTANTE: Nuevas variables
)
from GoogleNews import GoogleNews
import google.generativeai as genai

from groq import Groq

genai.configure(api_key=GEMINI_API_KEY)

class NewsIntel:
    def __init__(self):
        self.googlenews = GoogleNews(lang='en', period='1d') # Noticias de últimas 24h
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        self.model_premium = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- NIVEL 2: EL TANQUE (Google 2.0) ---
        # Aparece en tu lista como 'models/gemini-2.0-flash'. Es rápido y estable.
        self.model_backup_google = genai.GenerativeModel('gemini-2.0-flash')

        # --- NIVEL 3: LA EMERGENCIA (Groq) ---
        # Si Google falla totalmente, usamos Llama 3 en Groq.
        if GROQ_API_KEY:
            self.groq_client = Groq(api_key=GROQ_API_KEY)
        else:
            self.groq_client = None


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

        # 3. LÓGICA DE TRIPLE RESPALDO 🔥
        clean_json = ""
        
        # --- INTENTO 1: Google Gemini 2.5 ---
        try:
            response = self.model_premium.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
        except Exception as e:
            print(f"   ⚠️ Gemini 2.5 falló (Cuota). Probando Gemini 2.0...")
            
            # --- INTENTO 2: Google Gemini 2.0 ---
            try:
                response = self.model_backup_google.generate_content(prompt)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
            except Exception as e2:
                print(f"   ⚠️ Gemini 2.0 falló. Probando Groq (Llama 3)...")
                
                # --- INTENTO 3: Groq (Llama 3) ---
                if self.groq_client:
                    try:
                        chat_completion = self.groq_client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": "You are a financial analyst JSON machine."},
                                {"role": "user", "content": prompt}
                            ],
                            model="llama-3.3-70b-versatile", # Modelo muy potente y gratis en Groq
                            temperature=0,
                        )
                        clean_json = chat_completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    except Exception as e3:
                        print(f"❌ Error Fatal (Fallaron las 3 IAs): {e3}")
                        return {"score": 50, "decision": "ERROR", "reason": "Fallo Total IA"}
                else:
                    return {"score": 50, "decision": "ERROR", "reason": "Fallo Google y sin Groq Key"}

        # 4. PARSEO FINAL
        try:
            import json
            return json.loads(clean_json)
        except:
            return {"score": 50, "decision": "ERROR", "reason": "Error leyendo JSON"}
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

    # --- AYUDANTES PARA PRECIO INDIVIDUAL (TRADINGVIEW) ---
    # --- AYUDANTES PARA PRECIO INDIVIDUAL ---
    
    def _fetch_tv_price_stock(self, symbol: str, markets: list) -> float:
        """Busca el precio de UNA acción en TradingView Scanner."""
        url = 'https://scanner.tradingview.com/global/scan'
        # Ajuste para Yahoo/TV: Si viene con .BA, quitamos para TV, o viceversa si fuera necesario.
        clean_symbol = symbol.replace(".BA", "")
        
        payload = {
            "columns": ["close"],
            "filter": [
                {"left": "name", "operation": "equal", "right": clean_symbol.upper()}
            ],
            "options": {"lang": "es"},
            "markets": markets,
            "range": [0, 1]
        }
        try:
            r = requests.post(url, headers=TV_HEADERS, cookies=TV_COOKIES, json=payload, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data['data']:
                    price = data['data'][0]['d'][0]
                    print(f"   ✅ TV Stock ({symbol}): ${price}")
                    return float(price)
        except Exception:
            pass
        return 0.0

    def _fetch_cmc_price(self, symbol: str) -> float:
        """Fuente #1 para Cryptos: CoinMarketCap."""
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}
            r = requests.get(url, headers=self.cmc_headers, params=params, timeout=7)
            if r.status_code == 200:
                data = r.json()
                # CMC puede devolver varios para el mismo símbolo, tomamos el primero (mayor rank)
                if symbol.upper() in data['data']:
                    crypto_data = data['data'][symbol.upper()]
                    # Si es una lista (varios tokens con mismo nombre), tomamos el [0]
                    if isinstance(crypto_data, list):
                        price = crypto_data[0]['quote']['USD']['price']
                    else:
                        price = crypto_data['quote']['USD']['price']
                    
                    print(f"   ✅ CMC Crypto ({symbol}): ${price}")
                    return float(price)
        except Exception as e:
            print(f"   ⚠️ CMC Error ({symbol}): {e}")
            pass
        return 0.0

    def _fetch_binance_price(self, symbol: str) -> float:
        """Fuente #2 para Cryptos: Binance."""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                price = r.json()['price']
                print(f"   ✅ Binance Crypto ({symbol}): ${price}")
                return float(r.json()['price'])
        except: pass
        return 0.0

    def _fetch_tv_price_crypto(self, symbol: str) -> float:
        """Fuente #3 para Cryptos: TradingView Crypto."""
        payload = {
            "columns": ["close"],
            "filter": [{"left": "base_currency", "operation": "equal", "right": symbol.upper()}],
            "options": {"lang": "es"},
            "markets": ["coin"],
            "range": [0, 1]
        }


        try:
            r = requests.post(TV_COIN_URL, headers=TV_HEADERS, cookies=TV_COOKIES, json=payload, timeout=5)
            if r.status_code == 403:
                msg = "⚠️ **ALERTA CRÍTICA** ⚠️\nLas Cookies de TradingView han expirado (Error 403).\nPor favor actualiza `config.py` inmediatamente."
                print(f"❌ {msg}")
                Notifier.send_telegram_alert(msg)
                return pd.DataFrame()
            
            if r.status_code == 200 and r.json()['data']:

                price = r.json()['price']
                print(f"   ✅ TradingView Crypto ({symbol}): ${price}")

                return float(r.json()['data'][0]['d'][0])
        except: pass
        return 0.0

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
        
        if "argentina" in target_markets:
            sort_criteria = "volume"
            min_volume = 1000  # Filtro extra: Si no mueve al menos 1000 nominales, ni me lo traigas
        else:
            sort_criteria = "market_cap_basic"
            min_volume = 0

        payload = {
            "columns": TV_COLUMNS,
            "ignore_unknown_fields": False,
            "options": {"lang": "es"},
            "range": [0, limit],
            "sort": {"sortBy": sort_criteria, "sortOrder": "desc"}, # <--- AQUÍ ESTÁ LA MAGIA
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
                    # FILTRO EXTRA: Excluir activos sin liquidez (elimina basura muerta)
                    {"expression": {"left": "volume", "operation": "greater", "right": min_volume}},
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
        """
        if df_completo.empty: return pd.DataFrame()

        # --- CAMBIO CRÍTICO AQUÍ ---
        # Agregamos 'market_cap_basic' para poder hacer el ranking Top 30 después.
        columnas_deseadas = TV_RAW_LISTS[2] + ['close', 'change', 'volume', 'description', 'market_cap_basic']
        
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
        Lógica de Prioridades:
        1. Si es MERVAL (Lista) -> TradingView ARG -> Yahoo.
        2. Si es STOCK USA (Lista) -> TradingView USA -> Yahoo.
        3. TODO LO DEMÁS -> Asumimos CRYPTO -> CoinMarketCap -> Binance -> TV Crypto.
        """
        symbol = symbol.upper()
        
        # --- Listas de Identificación ---
        # Ampliamos la detección de Merval con la lista que pasaste antes
        merval_tickers = [
            "YPFD", "GGAL", "BMA", "PAMP", "TECO2", "TXAR", "ALUA", "CRES", "TGSU2", "TGNO4",
            "EDN", "TRAN", "CEPU", "SUPV", "BYMA", "VALO", "CVH", "LOMA", "MIRG", "BHIP",
            "BBAR", "BBARB", "COME", "MOLI", "LEDE", "SEMI", "MORI", "MOLA", "SAMI", "AGRO",
            "INVJ", "GCLA", "GAMI", "GCDI", "CTIO", "GARO", "FERR", "RIGO", "LONG", "DOME", 
            "RICH", "ROSE", "CELU", "CGPA2", "DGCE", "ECOG", "GBAN", "METR", "METRC", "HARG", 
            "HSAT", "IEB", "A3", "VIST", "MELI", "GLOB", "ELP", "PBR", "TEN", "DESP", "BIOX",

            # AGREGADOS FALTANTES (CEDEARS Y GENERAL)
            "HOOD", "INTR", "POLL", "URA", "BOLT", "OEST", "AUSO", "DGCU2", "CAPX"
        ]
        
        # Unimos con la watchlist de config por si acaso
        all_merval = set(merval_tickers + WATCHLIST_MERVAL)
        
        # 1. DETECCIÓN: ¿ES MERVAL?
        if symbol in all_merval or symbol.endswith(".BA"):
            price_ars = 0.0
            
            # Intentamos TradingView
            price_ars = self._fetch_tv_price_stock(symbol, ["argentina"])
            
            # Si falla, Backup Yahoo Finance
            if price_ars == 0:
                try:
                    yf_sym = f"{symbol}.BA" if not symbol.endswith(".BA") and "." not in symbol else symbol
                    price_ars = yf.Ticker(yf_sym).fast_info.last_price or 0.0
                except: pass

            # --- CONVERSIÓN OBLIGATORIA A USD ---
            if price_ars > 0:
                ccl = self.get_dolar_ccl() # Usamos tu método existente
                if ccl > 0:
                    price_usd = price_ars / ccl
                    print(f"💱 Conversión {symbol}: ${price_ars} ARS / {ccl} = ${price_usd:.2f} USD")
                    return price_usd
                else:
                    return price_ars # Fallback si no hay ccl (raro)
            
            return 0.0

        # 2. DETECCIÓN: ¿ES STOCK USA? (Solo los de tu Watchlist explícita)
        elif symbol in WATCHLIST_STOCKS:
            # print(f"🔎 Buscando {symbol} en STOCKS USA...")
            price = self._fetch_tv_price_stock(symbol, ["america"])
            if price > 0: return price
            print(f"🔎 Buscando {symbol} en STOCKS USA...")
            # Backup Yahoo
            try: return yf.Ticker(symbol).fast_info.last_price or 0.0
            except: pass

        # 3. TODO LO DEMÁS: ASUMIMOS CRYPTO (Prioridad CMC)
        else:
            # print(f"🔎 Buscando {symbol} en CRYPTO (CMC/Binance)...")
            
            # Opción A: CoinMarketCap (Tu preferida)
            price = self._fetch_cmc_price(symbol)
            if price > 0: return price
            
            # Opción B: Binance (Muy rápida para las comunes)
            price = self._fetch_binance_price(symbol)
            if price > 0: return price
            
            # Opción C: TradingView Crypto (Respaldo final para raras como HYPE)
            price = self._fetch_tv_price_crypto(symbol)
            if price > 0: return price

        print(f"❌ No se encontró precio para {symbol}")
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

    def find_market_opportunities(self, market_type: str, threshold: float, tier1_threshold: float) -> List[dict]:
        """
        Escáner Universal Híbrido V2.
        - CRYPTO: Top 50 (Rank) vs Resto [INTACTO].
        - USA/MERVAL: Top 30 (Market Cap) vs Resto [NUEVO].
        """
        print(f"📡 Escaneando {market_type}...")
        
        filtered = pd.DataFrame()
        col_change = 'change'     
        conversion_rate = 1.0
        # ==========================================================
        # 1. ESTRATEGIA CRYPTO (INTACTA - NO TOCAR)
        # ==========================================================
        if market_type == 'CRYPTO':
            # Traemos 300 para tener Top 50 + 250 alts para buscar gemas
            df_raw = self.scan_coin_market(limit=300)
            df = self._process_crypto_technicals(df_raw)
            
            if not df.empty and 'crypto_total_rank' in df.columns:
                df['crypto_total_rank'] = pd.to_numeric(df['crypto_total_rank'], errors='coerce').fillna(999)
                
                # Tier 1 Crypto
                #THRESHOLD_TIER_1 = -2.5 
                mask_top50 = (df['crypto_total_rank'] <= 50) & (df['change'] <= tier1_threshold)
                df_tier1 = df[mask_top50].copy()
                
                # Tier 2 Crypto
                mask_tier2 = (df['crypto_total_rank'] > 50) & (df['change'] <= threshold)
                df_tier2 = df[mask_tier2].copy()
                df_tier2 = df_tier2.sort_values(by='change', ascending=True).head(4)
                
                print(f"   📊 Crypto Tier 1 (Top 50): {len(df_tier1)} detectadas (Thresh: {tier1_threshold}%)")
                print(f"   📊 Crypto Tier 2 (Risk):   {len(df_tier2)} detectadas (Thresh: {threshold}%)")
                
                filtered = pd.concat([df_tier1, df_tier2])
            else:
                filtered = df 
        
        # ==========================================================
        # 2. ESTRATEGIA STOCKS (USA & MERVAL) - LÓGICA TIER 1 vs TIER 2
        # ==========================================================
        elif market_type in ['USA', 'MERVAL']:
            # A. Configuración específica por mercado
            if market_type == 'USA':
                df_raw = self.scan_tradingview(markets=["america"], limit=800)
                min_vol = 50000 
            else: # MERVAL
                df_raw = self.scan_tradingview(markets=["argentina"], limit=600)
                min_vol = 0
                
            
            if market_type == 'MERVAL':
                ccl = self.get_dolar_ccl() # Usamos tu nuevo método
                conversion_rate = 1 / ccl if ccl > 0 else 0
                print(f"🔄 Aplicando conversión Merval: Divisor {ccl}")
            # ----------------------------------

            df = self._process_technicals(df_raw)
            col_change = 'change'

            # 🔥🔥 1. FILTRO DE LIMPIEZA INICIAL (Whitelisting) 🔥🔥

            
            if market_type == 'MERVAL' and not df.empty and 'description' in df.columns:
                
                # A. Función para detectar si es una variante "sucia" (D, C, Warrant)
                def es_variante_sucia(symbol):
                    sym = symbol.upper()
                    # 1. Warrants (CRE3W)
                    if 'W' in sym or 'WARRANT' in row.get('description', '').upper(): return True
                    # 2. Bonos / Obligaciones (terminan en O, D, C y tienen numeros raros)
                    if len(sym) > 5 and any(c.isdigit() for c in sym): return True
                    # 3. Variantes de Liquidación (Terminan en D, DD, C, pero no son tickers válidos como EDN)
                    # Lista de tickers validos que TERMINAN en D o C (Excepciones)
                    valid_ends = ["YPFD", "PAMP", "TGSU2", "TECO2", "CEPU"] 
                    
                    if sym not in valid_ends:
                        if sym.endswith("D") or sym.endswith("DD") or sym.endswith("C") or sym.endswith("B"):
                            # Si termina en D pero la raíz existe en el DF (ej: existe PAMP y PAMPD), es sucia.
                            root = sym.rstrip("DCB")
                            if root in df['name'].values: return True
                            
                    return False

                # B. Aplicamos el filtro fila por fila
                indices_sucios = []
                for idx, row in df.iterrows():
                    if es_variante_sucia(row['name']):
                        indices_sucios.append(idx)
                
                df = df.drop(indices_sucios)
                print(f"   🧹 Limpieza Merval: Se eliminaron {len(indices_sucios)} variantes sucias.")

                cedear_keywords = 'CEDEAR|CERT DEP|ARG REPR|CERTIFICADO|DEPOSITO'
                es_cedear = df['description'].str.contains(cedear_keywords, case=False, regex=True)
                
                # LISTA COMPLETA DE ACCIONES ARGENTINAS PURAS + VIPS
                whitelist = [
                    # --- TOP TIER & SEGUNDA LÍNEA (Líderes) ---
                    "YPFD", "GGAL", "PAMP",
                    "BMA", "BBAR", "TXAR", "ALUA", "CEPU", "TGSU2", "LOMA", "MIRG", "BHIP",
                    "BBAR", "BBARB", "COME","MOLI", "LEDE", "SEMI", "MORI" 
                    
                    # --- PANEL GENERAL (Agro, Industria, Gas, Pequeñas) ---
                    "TECO2", "CRES", "EDN", "TRAN", "TGNO4", 
                    "SUPV", "BYMA", "VALO", "LOMA", "COME", "GLOB",
                    "HARG", "HSAT", "IRCP", "IRSA", "JMIN", "LEAL", "MADX", "MAXI", "NAHU", 
                    
                    # --- VIPS / REGIONALES (Cedears permitidos) ---
                    "VIST", "MELI", "GLOB", "ELP"
                ]
                
                es_permitido = df['name'].isin(whitelist)
                
                # Nos quedamos con: (NO es Cedear) O (Está en la Whitelist)
                mask_final = (~es_cedear) | (es_permitido)
                df = df[mask_final].copy()
                print(f"   🇦🇷 Filtro Merval: Quedan {len(df)} activos (Locales + VIPs).")

            # 🔥🔥 2. DIVISIÓN DE TIERS Y FILTRADO DE PRECIO 🔥🔥
            if not df.empty and 'market_cap_basic' in df.columns:
                df['market_cap_basic'] = pd.to_numeric(df['market_cap_basic'], errors='coerce').fillna(0)
                if min_vol > 0 and 'volume' in df.columns:
                    df = df[df['volume'] > min_vol]
                
                # Ordenamos por Market Cap
                df = df.sort_values(by='market_cap_basic', ascending=False)

                # --- LÓGICA DE SEPARACIÓN (Aquí está el cambio clave) ---
                if market_type == 'MERVAL':
                    # Regla: Tier 1 son las Locales/VIP. Tier 2 son los ADRs "colados".
                    mask_extranjera = df['description'].str.contains('ADR|CEDEAR|CERT DEP|ARG REPR', case=False, regex=True)
                    
                    # VIPs que forzamos a Tier 1 aunque sean Cedears
                    vip_list = ['MELI', 'VIST', 'GLOB', 'PBR', 'TEN', 'TX']
                    es_vip = df['name'].isin(vip_list)
                    
                    mask_t1_candidatos = (~mask_extranjera) | es_vip
                    
                    df_tier1_candidates = df[mask_t1_candidatos].copy()
                    df_tier2_candidates = df[~mask_t1_candidatos].copy() # El resto (ADRs comunes)
                
                else: # USA
                    # Regla Clásica: Top 30 vs Resto
                    TOP_N = 30
                    limit_index = min(len(df), TOP_N)
                    df_tier1_candidates = df.iloc[:limit_index]
                    df_tier2_candidates = df.iloc[limit_index:]

                # --- APLICACIÓN DE THRESHOLDS ---
                
                # Tier 1 (Blue Chips) -> tier1_threshold
                mask_t1 = (df_tier1_candidates[col_change] <= tier1_threshold)
                df_tier1 = df_tier1_candidates[mask_t1].copy()
                df_tier1['tier_label'] = "🏢 BLUE CHIP"

                # Tier 2 (Riesgo/ADRs) -> threshold + Limite 4
                mask_t2 = (df_tier2_candidates[col_change] <= threshold)
                df_tier2 = df_tier2_candidates[mask_t2].copy()
                df_tier2 = df_tier2.sort_values(by=col_change, ascending=True).head(4)
                df_tier2['tier_label'] = "🚀 SPECULATIVE"

                print(f"   📊 {market_type} Tier 1 (Safe): {len(df_tier1)} detectadas (< {tier1_threshold}%)")
                print(f"   📊 {market_type} Tier 2 (Risk): {len(df_tier2)} detectadas (< {threshold}%)")

                filtered = pd.concat([df_tier1, df_tier2])
            
            else:
                print("⚠️ No se encontró Market Cap, aplicando filtro simple.")
                if not df.empty:
                    filtered = df[df[col_change] <= threshold].copy()

        # ==========================================================
        # 3. PROCESAMIENTO COMÚN Y SALIDA
        # ==========================================================
        if filtered.empty: return []

        # Deduplicación de nombres (Anti-Spam de acciones con Tickers repetidos o ADRs sucios)
        if 'description' in filtered.columns:
            def clean_name(text):
                if not isinstance(text, str): return str(text)
                text = text.upper()
                noise_words = [" CEDEAR", " ADR", " S.A.", " SA", " INC.", " CORP", " LTD", " SHS", " CL A"]
                for word in noise_words: text = text.replace(word, "")
                return " ".join(text.split()[:2])

            filtered['clean_id'] = filtered['description'].apply(clean_name)
            filtered = filtered.drop_duplicates(subset=['clean_id'], keep='first')

        opportunities = []

        for _, row in filtered.iterrows():
            rsi = row.get('RSI', 50)
            patron = row.get('Patrones_Hoy')
            tier = row.get('tier_label', '') # Recuperamos si es Blue Chip o Speculative
            
            tech_msg = []
            # Agregamos la etiqueta al mensaje técnico visualmente
            if market_type == 'CRYPTO':
                 rank = row.get('crypto_total_rank', 999)
                 tech_msg.append("🏆 TOP 50" if rank <= 50 else "⚡ GEM/RISK")
            elif tier:
                 tech_msg.append(tier)
            
            if patron: tech_msg.append(f"🕯️ {patron}")
            if rsi < 30: tech_msg.append(f"💎 Oversold ({round(rsi)})")
            
            signal_reason = " | ".join(tech_msg) if tech_msg else "Dip detected"
            
            symbol = row.get('base_currency', row.get('name'))
            name = row.get('base_currency_desc', row.get('description', symbol))

            opportunities.append({
                "symbol": symbol,
                "name": name,
                "price": float(row['close']) * conversion_rate,
                "percent_change": float(row[col_change]),
                "rsi": float(rsi) if pd.notna(rsi) else 50,
                "technical_signal": signal_reason,
                "ai_score": None, "ai_decision": None, "ai_reason": None
            })

        return opportunities
    

    
    
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
    
    def get_dolar_ccl(self) -> float:
        """Obtiene la cotización del Dólar CCL (o Blue) para convertir pesos."""
        try:
            # DolarApi.com es gratuita y muy usada en Arg
            r = requests.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=3)
            if r.status_code == 200:
                data = r.json()
                price = float(data['venta']) # Usamos punta vendedora
                print(f"💵 Dólar CCL detectado: ${price}")
                return price
        except Exception as e:
            print(f"⚠️ Error obteniendo Dólar CCL: {e}")
        
        return 1200.0 # Fallback de emergencia (Actualizar según economía real)

    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
        ]