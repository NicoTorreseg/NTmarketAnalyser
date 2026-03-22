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
        
        # Filtramos estrictamente por la nueva regla de RSI dinámica
        valid_ops = []
        for op in ops:
            if bot._is_valid_technical(market, op.get('tier', ''), op.get('rsi'), op.get('percent_change') or op.get('percent_change_24h', 0)):
                valid_ops.append(op)
                
        print(f"✅ Se validaron {len(valid_ops)} oportunidades estrictas (RSI+Drop) de {len(ops)} iniciales en {market}.\n")
        
        if not valid_ops:
            continue
            
        # Vamos a probar solo los primeros 2 de cada mercado para no quemar la API de LLM rápido
        for op in valid_ops[:2]:
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
                    tier = op.get('tier', 'UNKNOWN')
                    size = bot._calculate_position_size(score, bounce, tier)
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
