# Configuraciones globales del proyecto
# En el futuro, podrías leer esto desde variables de entorno con os.getenv()
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# Ahora leemos desde el sistema, no desde el código escrito
CMC_API_KEY = os.getenv("CMC_API_KEY")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
USE_MOCK_DATA = False
SQLALCHEMY_DATABASE_URL = "sqlite:///./crypto_ops.db"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# CONFIGURACIÓN STOCKS (YAHOO FINANCE)
# Lista de empresas tecnológicas y populares para monitorear
WATCHLIST_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", 
    "NFLX", "AMD", "INTC", "BABA", "PYPL", "UBER", "COIN"
]

# --- NUEVA CONFIGURACIÓN: MERVAL (ARGENTINA) ---
# Tickers de Yahoo Finance terminan en .BA para Buenos Aires
# Acciones argentinas que cotizan en Wall Street (NYSE/NASDAQ).
# Al no tener el sufijo .BA, Yahoo Finance traerá el precio en Dólares.
WATCHLIST_MERVAL = [
    "YPF",      # YPF S.A.
    "GGAL",     # Grupo Financiero Galicia
    "BMA",      # Banco Macro
    "BBAR",     # BBVA Argentina
    "SUPV",     # Grupo Supervielle
    "PAM",      # Pampa Energía
    "CEPU",     # Central Puerto
    "TGS",      # Transportadora de Gas del Sur
    "EDN",      # Edenor
    "TEO",      # Telecom Argentina
    "LOMA",     # Loma Negra (Cementos)
    "CRESY",    # Cresud (Agro)
    "IRS",      # IRSA (Inversiones y Representaciones)
    "TX",       # Ternium S.A.
    "VIST",     # Vista Energy (Vaca Muerta)
    "MELI",     # MercadoLibre (La gigante del ecommerce)
    "GLOB",     # Globant (Software)
    "DESP",     # Despegar
    "BIOX"      # Bioceres Crop Solutions
]


TV_HEADERS = {
    'accept': 'application/json',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://es.tradingview.com',
    'referer': 'https://es.tradingview.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

TV_COOKIES = {

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

    # Si TV te bloquea en el futuro, actualiza estas cookies desde el navegador
}

# Listas de datos (Copiadas exactamente de tu script exitoso)
TV_RAW_LISTS = [
    # Lista 1: Info General
    ["name","description","logoid","update_mode","type","typespecs","close","pricescale","minmov","fractional","minmove2","currency","change","volume","relative_volume_10d_calc","market_cap_basic","fundamental_currency_code","price_earnings_ttm","earnings_per_share_diluted_ttm","earnings_per_share_diluted_yoy_growth_ttm","dividends_yield_current","sector.tr","market","sector","AnalystRating","AnalystRating.tr","exchange"],
    # Lista 2: Performance
    ["name","description","logoid","update_mode","type","typespecs","close","pricescale","minmov","fractional","minmove2","currency","change","Perf.W","Perf.1M","Perf.3M","Perf.6M","Perf.YTD","Perf.Y","Perf.5Y","Perf.10Y","Perf.All","Volatility.W","Volatility.M","exchange"],
    # Lista 3: TÉCNICOS Y VELAS
    ["name","description","logoid","update_mode","type","typespecs","TechRating_1D","TechRating_1D.tr","MARating_1D","MARating_1D.tr","OsRating_1D","OsRating_1D.tr","RSI","Mom","pricescale","minmov","fractional","minmove2","AO","CCI20","Stoch.K","Stoch.D","Candle.3BlackCrows","Candle.3WhiteSoldiers","Candle.AbandonedBaby.Bearish","Candle.AbandonedBaby.Bullish","Candle.Doji","Candle.Doji.Dragonfly","Candle.Doji.Gravestone","Candle.Engulfing.Bearish","Candle.Engulfing.Bullish","Candle.EveningStar","Candle.Hammer","Candle.HangingMan","Candle.Harami.Bearish","Candle.Harami.Bullish","Candle.InvertedHammer","Candle.Kicking.Bearish","Candle.Kicking.Bullish","Candle.LongShadow.Lower","Candle.LongShadow.Upper","Candle.Marubozu.Black","Candle.Marubozu.White","Candle.MorningStar","Candle.ShootingStar","Candle.SpinningTop.Black","Candle.SpinningTop.White","Candle.TriStar.Bearish","Candle.TriStar.Bullish","exchange"]
]

# Lista aplanada lista para enviar a la API
TV_COLUMNS = list(set(item for sublist in TV_RAW_LISTS for item in sublist))


TV_COIN_URL = "https://scanner.tradingview.com/coin/scan"

# Listas unificadas para Cripto (General + Performance + Técnicos)
TV_COIN_LISTS = [
    ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","close","pricescale","minmov","fractional","minmove2","currency","24h_close_change|5","market_cap_calc","fundamental_currency_code","24h_vol_cmc","circulating_supply","24h_vol_to_market_cap","socialdominance","crypto_common_categories.tr","TechRating_1D","TechRating_1D.tr"],
    ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","market_cap_calc","fundamental_currency_code","24h_close_change|5","Perf.W","Perf.1M","Perf.3M","Perf.6M","Perf.YTD","Perf.Y","Perf.5Y","Perf.10Y","Perf.All","Volatility.D"],
    ["base_currency","base_currency_desc","base_currency_logoid","update_mode","type","typespecs","exchange","crypto_total_rank","TechRating_1D","TechRating_1D.tr","MARating_1D","MARating_1D.tr","OsRating_1D","OsRating_1D.tr","RSI","Mom","pricescale","minmov","fractional","minmove2","AO","CCI20","Stoch.K","Stoch.D","Candle.3BlackCrows","Candle.3WhiteSoldiers","Candle.AbandonedBaby.Bearish","Candle.AbandonedBaby.Bullish","Candle.Doji","Candle.Doji.Dragonfly","Candle.Doji.Gravestone","Candle.Engulfing.Bearish","Candle.Engulfing.Bullish","Candle.EveningStar","Candle.Hammer","Candle.HangingMan","Candle.Harami.Bearish","Candle.Harami.Bullish","Candle.InvertedHammer","Candle.Kicking.Bearish","Candle.Kicking.Bullish","Candle.LongShadow.Lower","Candle.LongShadow.Upper","Candle.Marubozu.Black","Candle.Marubozu.White","Candle.MorningStar","Candle.ShootingStar","Candle.SpinningTop.Black","Candle.SpinningTop.White","Candle.TriStar.Bearish","Candle.TriStar.Bullish"]
]

# Aplanamos la lista eliminando duplicados
TV_COIN_COLUMNS = list(set(item for sublist in TV_COIN_LISTS for item in sublist))



# --- NUEVA CONFIGURACIÓN PARA NOTIFICACIONES ---
# 1. Busca "BotFather" en Telegram, crea un bot y pega el token aquí:
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 2. Busca "userinfobot" en Telegram para saber tu ID numérico y pégalo aquí:

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Horarios de ejecución automática (formato 24hs)
SCHEDULE_HOURS = [9, 13, 22]