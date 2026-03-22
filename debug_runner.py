import json
import time
from AppServices import MarketAnalyzer, NewsIntel
from BotServices import TradingBot
from database import SessionLocal

def run_debug_env():
    print("==============================================")
    print("🚀 INICIANDO ENTORNO DE DEBUG PROFUNDO 🚀")
    print("==============================================")
    
    analyzer = MarketAnalyzer()
    intel = NewsIntel()
    db = SessionLocal()
    bot = TradingBot(db)
    
    markets = [
        ('USA', -2.0, -1.5), 
        ('MERVAL', -2.0, -1.5), 
        ('CRYPTO', -3.0, -2.0)
    ]
    
    for market, threshold, tier1 in markets:
        print("\n\n" + "="*50)
        print(f"📡 ESCANEANDO MERCADO: {market}")
        print("="*50)
        
        ops = analyzer.find_market_opportunities(market, threshold, tier1)
        print(f"✅ Se encontraron {len(ops)} oportunidades técnicas en {market}.\n")
        
        if not ops:
            continue
            
        # Vamos a probar solo los primeros 2 de cada mercado para no quemar la API de LLM rapido
        for op in ops[:2]:
            symbol = op['symbol']
            name = op.get('name', symbol)
            price = op['price']
            pct = op.get('percent_change') or op.get('percent_change_24h', 0)
            rsi = op.get('rsi', 50)
            
            print(f"\n------------------------------------------------")
            print(f"🔍 ANALIZANDO ACTIVO: {symbol} ({name})")
            print(f"📉 TÉCNICO -> Precio: ${price:.2f} | Caída {pct}% | RSI: {rsi}")
            
            is_crypto = (market == 'CRYPTO')
            is_merval = (market == 'MERVAL')
            
            # --- DEBUG DE NOTICIAS ---
            # Vamos a ver qué lee el bot realmente antes de pasarlo a la IA
            if is_merval:
                intel.googlenews.clear()
                intel.googlenews.lang = 'es'
                intel.googlenews.region = 'AR'
                clean_name = name.split(' inc')[0].split(' S.A.')[0].split(' Corp')[0]
                search_term = f"{clean_name} acciones economía"
            else:
                intel.googlenews.clear()
                intel.googlenews.lang = 'en'
                if is_crypto:
                    search_term = f"{name} cryptocurrency" if name else f"{symbol} crypto coin"
                else:
                    search_term = f"{symbol} stock news"
            
            print(f"📰 BUSCANDO NOTICIAS: '{search_term}'...")
            try:
                intel.googlenews.search(search_term)
                results = intel.googlenews.result()
                if not results and is_merval:
                     intel.googlenews.search(f"{symbol} acciones merval")
                     results = intel.googlenews.result()
                
                print(f"📝 Se encontraron {len(results)} titulares. Los top 3 son:")
                for res in results[:3]:
                    print(f"   - {res['title']} ({res.get('media', 'Unkown')})")
            except Exception as e:
                print(f"❌ Error buscando noticias: {e}")
                
            # --- DEBUG DE IA ---
            print("\n🤖 CONSULTANDO A LA INTELIGENCIA ARTIFICIAL...")
            try:
                ai_analysis = intel.get_sentiment_analysis(
                    symbol=symbol, 
                    asset_name=name, 
                    is_crypto=is_crypto, 
                    is_merval=is_merval
                )
                
                decision = ai_analysis.get('decision', 'N/A')
                score = ai_analysis.get('score', 0)
                bounce = ai_analysis.get('bounce_probability', 50)
                reason = ai_analysis.get('reason', 'Sin datos')
                
                print(f"🎯 DECISIÓN: {decision}")
                print(f"📊 SCORE IA: {score}/100")
                print(f"📈 PROB REBOTE: {bounce}%")
                print(f"🗣️ TESIS: {reason}")
                
                # --- DEBUG DE CAPITAL ---
                if decision == "BUY":
                    size = bot._calculate_position_size(score, bounce)
                    print(f"\n💰 CAPITAL A INVERTIR: ${size:.2f} USD")
                else:
                    print("\n🛑 NO SE EJECUTA COMPRA (No alcanzó el threshold de BUY o Score).")
                
            except Exception as e:
                 print(f"❌ Error IA: {e}")
                 
            print("⏳ Pausa anti-spam de IA (5s)...")
            time.sleep(5)
            
    print("\n==============================================")
    print("✅ CICLO DE DEBUG FINALIZADO")
    print("==============================================")

if __name__ == "__main__":
    run_debug_env()
