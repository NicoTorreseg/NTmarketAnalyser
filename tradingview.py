import requests
import pandas as pd
import matplotlib.pyplot as plt

cookies = {
    'cookiePrivacyPreferenceBannerProduction': 'notApplicable',
    '_ga': 'GA1.1.2138358240.1758657294',
    'cookiesSettings': '{"analytics":true,"advertising":true}',
    '_sp_ses.cf1a': '*',
    'device_t': 'R2RUSEFROjA.CpXhRBVx5BDHKthfGZKxfVB0B56QgnHilY6BTuQ4FnU',
    'sessionid': 'ktcuhuk8jg95x7qpdqfg3nswd8qaaifh',
    'sessionid_sign': 'v3:JPUNNkLVzWvuPNX00jX4u+dJLhK2sgtSS5+1Qh+x2x4=',
    '_ga_YVVRYGL0E0': 'GS2.1.s1764883414$o11$g1$t1764883649$j60$l0$h0',
    'png': '2c748bbe-012c-4945-86f5-3eb5c9c46386',
    'etg': '2c748bbe-012c-4945-86f5-3eb5c9c46386',
    'cachec': '2c748bbe-012c-4945-86f5-3eb5c9c46386',
    'tv_ecuid': '2c748bbe-012c-4945-86f5-3eb5c9c46386',
    '_sp_id.cf1a': '748e3439-a696-4d51-8cdb-196a4f2f1ff2.1758657294.8.1764883682.1763752481.4fe76deb-ffc6-47ec-b1cd-f45a97b9a37a.ae319b45-610a-4cef-afd1-6ab43c4ddcaf.7a37d3f7-182c-47c8-bd1e-739682cfdf6c.1764883414051.8',
}
headers = {
    'accept': 'application/json',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://es.tradingview.com',
    'referer': 'https://es.tradingview.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

# 1. CORRECCIÓN: Agregadas las comas que faltaban entre las listas
lists = [
    ["name","description","logoid","update_mode","type","typespecs","close","pricescale","minmov","fractional","minmove2","currency","change","volume","relative_volume_10d_calc","market_cap_basic","fundamental_currency_code","price_earnings_ttm","earnings_per_share_diluted_ttm","earnings_per_share_diluted_yoy_growth_ttm","dividends_yield_current","sector.tr","market","sector","AnalystRating","AnalystRating.tr","exchange"],
    ["name","description","logoid","update_mode","type","typespecs","close","pricescale","minmov","fractional","minmove2","currency","change","Perf.W","Perf.1M","Perf.3M","Perf.6M","Perf.YTD","Perf.Y","Perf.5Y","Perf.10Y","Perf.All","Volatility.W","Volatility.M","exchange"],
    ["name","description","logoid","update_mode","type","typespecs","market_cap_basic","fundamental_currency_code","Perf.1Y.MarketCap","price_earnings_ttm","price_earnings_growth_ttm","price_sales_current","price_book_fq","price_to_cash_f_operating_activities_ttm","price_free_cash_flow_ttm","price_to_cash_ratio","enterprise_value_current","enterprise_value_to_revenue_ttm","enterprise_value_to_ebit_ttm","enterprise_value_ebitda_ttm","exchange"],
    ["name","description","logoid","update_mode","type","typespecs","TechRating_1D","TechRating_1D.tr","MARating_1D","MARating_1D.tr","OsRating_1D","OsRating_1D.tr","RSI","Mom","pricescale","minmov","fractional","minmove2","AO","CCI20","Stoch.K","Stoch.D","Candle.3BlackCrows","Candle.3WhiteSoldiers","Candle.AbandonedBaby.Bearish","Candle.AbandonedBaby.Bullish","Candle.Doji","Candle.Doji.Dragonfly","Candle.Doji.Gravestone","Candle.Engulfing.Bearish","Candle.Engulfing.Bullish","Candle.EveningStar","Candle.Hammer","Candle.HangingMan","Candle.Harami.Bearish","Candle.Harami.Bullish","Candle.InvertedHammer","Candle.Kicking.Bearish","Candle.Kicking.Bullish","Candle.LongShadow.Lower","Candle.LongShadow.Upper","Candle.Marubozu.Black","Candle.Marubozu.White","Candle.MorningStar","Candle.ShootingStar","Candle.SpinningTop.Black","Candle.SpinningTop.White","Candle.TriStar.Bearish","Candle.TriStar.Bullish","exchange"]
]


listaunificada = list(set(item for sublist in lists for item in sublist))


COIN_LISTS = [
    ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","close","pricescale","minmov","fractional","minmove2","currency","24h_close_change|5","market_cap_calc","fundamental_currency_code","24h_vol_cmc","circulating_supply","24h_vol_to_market_cap","socialdominance","crypto_common_categories.tr","TechRating_1D","TechRating_1D.tr"],
    ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","market_cap_calc","fundamental_currency_code","24h_close_change|5","Perf.W","Perf.1M","Perf.3M","Perf.6M","Perf.YTD","Perf.Y","Perf.5Y","Perf.10Y","Perf.All","Volatility.D"],
    ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","TechRating_1D","TechRating_1D.tr","MARating_1D","MARating_1D.tr","OsRating_1D","OsRating_1D.tr","RSI","Mom","pricescale","minmov","fractional","minmove2","AO","CCI20","Stoch.K","Stoch.D","Candle.3BlackCrows","Candle.3WhiteSoldiers","Candle.AbandonedBaby.Bearish","Candle.AbandonedBaby.Bullish","Candle.Doji","Candle.Doji.Dragonfly","Candle.Doji.Gravestone","Candle.Engulfing.Bearish","Candle.Engulfing.Bullish","Candle.EveningStar","Candle.Hammer","Candle.HangingMan","Candle.Harami.Bearish","Candle.Harami.Bullish","Candle.InvertedHammer","Candle.Kicking.Bearish","Candle.Kicking.Bullish","Candle.LongShadow.Lower","Candle.LongShadow.Upper","Candle.Marubozu.Black","Candle.Marubozu.White","Candle.MorningStar","Candle.ShootingStar","Candle.SpinningTop.Black","Candle.SpinningTop.White","Candle.TriStar.Bearish","Candle.TriStar.Bullish"]
]
# Unificamos columnas
COIN_COLUMNS = list(set(item for sublist in COIN_LISTS for item in sublist))

def get_crypto_data(limit=100):
    """
    Nuevo scanner específico para 'Coins' (no pares repetidos).
    Endpoint: scanner.tradingview.com/coin/scan
    """
    url = 'https://scanner.tradingview.com/coin/scan'
    
    payload = {
        "columns": COIN_COLUMNS,
        "ignore_unknown_fields": False,
        "options": {"lang": "es"},
        "range": [0, limit],
        "sort": {"sortBy": "crypto_total_rank", "sortOrder": "asc"}, # Ranking real
        "symbols": {},
        "markets": ["coin"] # Clave para este endpoint
    }

    try:
        print(f"📡 Consultando Crypto Screener (Top {limit})...")
        response = requests.post(url, headers=headers, cookies=cookies, json=payload)
        
        if response.status_code == 200:
            json_data = response.json()
            if 'data' in json_data:
                df = pd.DataFrame([d['d'] for d in json_data['data']])
                
                # Asignar nombres de columnas si coinciden
                if len(df.columns) == len(COIN_COLUMNS):
                    df.columns = COIN_COLUMNS
                else:
                    print(f"⚠️ Ojo: Recibimos {len(df.columns)} columnas, esperábamos {len(COIN_COLUMNS)}")
                
                return df
            else:
                print("⚠️ Respuesta vacía de TV")
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

    return pd.DataFrame()

def procesar_crypto_tecnico(df_raw):
    """
    Limpia el DataFrame de Cripto:
    1. Renombra columnas raras (24h_close_change|5 -> Change).
    2. Traduce Velas (0/1 -> Texto).
    """
    if df_raw.empty: return df_raw

    df = df_raw.copy()

    # 1. Renombrar columna de cambio (TradingView usa este nombre interno raro)
    col_cambio = "24h_close_change|5"
    if col_cambio in df.columns:
        df.rename(columns={col_cambio: "change_24h"}, inplace=True)
    
    # 2. Detectar Patrones de Velas
    candle_cols = [c for c in df.columns if "Candle." in c]
    
    def detectar(row):
        patrones = []
        for col in candle_cols:
            if pd.notna(row[col]) and row[col] == 1:
                # Limpiar nombre: Candle.Hammer -> Hammer
                patrones.append(col.replace("Candle.", "").replace(".", " "))
        return ", ".join(patrones) if patrones else "Sin Patrón"

    if candle_cols:
        df['Patrones_Hoy'] = df.apply(detectar, axis=1)

    # 3. Seleccionar columnas finales limpias para ver en consola
    # Prioridad: Símbolo, Precio, Cambio, RSI, Patrón
    cols_view = ['base_currency', 'close', 'change_24h', 'RSI', 'Patrones_Hoy', 'TechRating_1D.tr']
    cols_existentes = [c for c in cols_view if c in df.columns]
    
    return df[cols_existentes + [c for c in df.columns if c not in cols_existentes]] # Reordenar


def make_request(markets=None, limit=100):
    """
    Realiza la petición a TradingView.
    :param markets: Lista de países (ej: ['argentina', 'america']). Si es None, usa una lista global.
    :param limit: Cantidad de resultados a traer (ej: 100, 500, 1000).
    """
    
    # Si no especificas mercados, usamos una selección de los principales del mundo
    if not markets:
        target_markets = [
            "america", "argentina", "brazil", "mexico", "germany", 
            "united_kingdom", "china", "japan", "spain", "france", 
            "italy", "india", "canada", "australia"
        ]
    else:
        target_markets = markets

    data = {
        "columns": listaunificada, # Usa la lista que unificamos arriba
        "ignore_unknown_fields": False,
        "options": {"lang": "es"},
        "range": [0, limit],  # Aquí aplica el límite dinámico (ej: Top 500)
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "symbols": {},
        "markets": target_markets, # Aquí aplica los mercados dinámicos
        "filter2": {
            "operator": "and",
            "operands": [
                {
                    "operation": {
                        "operator": "or",
                        "operands": [
                            # Acciones Comunes
                            {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "stock"}}, {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}]}},
                            # Acciones Preferentes
                            {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "stock"}}, {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}]}},
                            # DR (ADRs / Cedears)
                            {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "dr"}}]}},
                            # Fondos (excluyendo ETFs)
                            {"operation": {"operator": "and", "operands": [{"expression": {"left": "type", "operation": "equal", "right": "fund"}}, {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["etf"]}}]}}
                        ]
                    }
                },
                # Excluir Pre-IPO
                {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["pre-ipo"]}}
            ]
        }
    }

    # Usamos URL Global, pero filtramos con la lista 'markets' dentro del JSON
    url = 'https://scanner.tradingview.com/global/scan'
    
    try:
        # Usamos 'headers' y 'cookies' (en minúscula) que vienen de tus líneas 0-36
        response = requests.post(url, headers=headers, cookies=cookies, json=data)
        
        if response.status_code == 200:
            json_data = response.json()
            if 'data' in json_data:
                return pd.DataFrame([d['d'] for d in json_data['data']])
            else:
                print("⚠️ La respuesta no contiene datos.")
                return pd.DataFrame()
        else:
            print(f"❌ Error: {response.status_code}")
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return pd.DataFrame()


def generar_dataframe_tecnico(df_completo):
    """
    Toma el DataFrame gigante y extrae/limpia la lista de Análisis Técnico (Lista 3),
    pero preservando el precio (close) y el cambio (change) para dar contexto.
    """
    if df_completo.empty:
        return pd.DataFrame()

    # 1. Definimos qué columnas queremos: La Lista 3 + Las Clave de Precios
    # Agregamos manualmente 'close', 'change' y 'description' para tener contexto
    columnas_extra = ['close', 'change', 'description']
    columnas_tecnicas_deseadas = lists[3] + columnas_extra
    
    # Aseguramos que existan en el DF descargado (intersección de conjuntos)
    # Convertimos a set para eliminar duplicados si los hubiera
    cols_existentes = list(set(c for c in columnas_tecnicas_deseadas if c in df_completo.columns))
    
    # Creamos el sub-dataframe con todo lo necesario
    df_tech = df_completo[cols_existentes].copy()

    # 2. LÓGICA: Unificar Patrones de Velas
    candle_cols = [c for c in df_tech.columns if "Candle." in c]
    
    def detectar_patrones(row):
        encontrados = []
        for col in candle_cols:
            # Verificamos que sea 1 (y nos aseguramos que no sea NaN)
            if pd.notna(row[col]) and row[col] == 1: 
                nombre_limpio = col.replace("Candle.", "").replace(".", " ")
                encontrados.append(nombre_limpio)
        return ", ".join(encontrados) if encontrados else "Sin Patrón"

    if candle_cols:
        df_tech['Patrones_Hoy'] = df_tech.apply(detectar_patrones, axis=1)
    else:
        df_tech['Patrones_Hoy'] = "Sin Datos Velas"

    # 3. Limpieza Final: Ordenamos columnas con PRIORIDAD
    # Ahora sí incluimos close y change al principio
    cols_prioridad = ['name', 'close', 'change', 'RSI', 'Stoch.K', 'TechRating_1D.tr', 'Patrones_Hoy']
    
    # Filtramos solo las que existen
    cols_finales = [c for c in cols_prioridad if c in df_tech.columns]
    
    # Agregamos el resto
    otras_cols = [c for c in df_tech.columns if c not in cols_finales and c not in candle_cols]
    
    df_final = df_tech[cols_finales + otras_cols]
    
    return df_final
# --- ZONA DE PRUEBAS ---

if __name__ == "__main__":
    
    print("\n--- 📡 Obteniendo Datos Globales (Precios + Técnicos) ---")
    df_completo = make_request(markets=["america", "argentina"], limit=1000)
    
    if not df_completo.empty:
        # Asignar nombres a columnas del DF completo
        if len(df_completo.columns) == len(listaunificada):
            df_completo.columns = listaunificada

        print("\n--- 📊 Generando DataFrame Técnico Especializado ---")
        df_tecnico = generar_dataframe_tecnico(df_completo)
        
        # Filtro visual para la terminal (solo para ver que funcionó)
        con_patron = df_tecnico[df_tecnico['Patrones_Hoy'] != "Sin Patrón"]
        print(f"\n🕯️ Acciones con Patrones detectados ({len(con_patron)}):")
        
        cols_ver = ['name', 'close', 'change', 'RSI', 'Patrones_Hoy', 'TechRating_1D.tr']
        # Nos aseguramos de que las columnas existan antes de imprimir
        cols_ver = [c for c in cols_ver if c in con_patron.columns] 
        
        if not con_patron.empty:
            print(con_patron.sort_values(by='change')[cols_ver].head(10))

        # --- 💾 GUARDANDO EXCELS ---
        print("\n--- 💾 Guardando archivos Excel... ---")
        
        try:
            # 1. Excel Completo (Raw Data)
            nombre_completo = "TV_Data_Completa.xlsx"
            df_completo.to_excel(nombre_completo, index=False)
            print(f"✅ Archivo guardado: {nombre_completo}")

            # 2. Excel Técnico (Procesado y Limpio)
            nombre_tecnico = "TV_Analisis_Tecnico.xlsx"
            df_tecnico.to_excel(nombre_tecnico, index=False)
            print(f"✅ Archivo guardado: {nombre_tecnico}")
            
        except ImportError:
            print("❌ Error: Necesitas instalar openpyxl. Ejecuta: pip install openpyxl")
        except PermissionError:
            print("❌ Error: Cierra el archivo Excel si lo tienes abierto antes de guardar.")

    else:
        print("No se recibieron datos.")

    # PRUEBA 1: CRYPTO (Lo que te interesa ahora)
    print("\n--- 🪙 PROBANDO NUEVO CRYPTO SCREENER ---")
    df_crypto = get_crypto_data(limit=150)
    
    if not df_crypto.empty:
        print(f"✅ Se obtuvieron {len(df_crypto)} criptomonedas.")
        
        # Procesamos para ver datos legibles
        df_clean = procesar_crypto_tecnico(df_crypto)
        
        # Filtramos para ver si funciona la detección de velas
        con_patron = df_clean[df_clean['Patrones_Hoy'] != "Sin Patrón"]
        
        print(f"\n🕯️ Criptos con Patrones de Velas Hoy ({len(con_patron)}):")
        # Mostramos las primeras 10, ordenadas por ranking
        print(con_patron[['base_currency', 'close', 'change_24h', 'Patrones_Hoy']].head(10))
        
        # Filtramos los DIPS (Caídas > 5%)
        dips = df_clean[df_clean['change_24h'] < -3.0]
        print(f"\n📉 DIPS Detectados (Caída > 3%): {len(dips)}")
        if not dips.empty:
             print(dips[['base_currency', 'close', 'change_24h', 'RSI']].head(5))

        # Guardar Excel de prueba
        try:
            df_clean.to_excel("Test_Crypto_Data.xlsx", index=False)
            print("\n💾 Guardado 'Test_Crypto_Data.xlsx'")
        except: pass

    else:
        print("❌ No se obtuvieron datos de Cripto.")


