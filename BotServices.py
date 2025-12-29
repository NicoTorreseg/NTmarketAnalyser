# BotServices.py
import json
import time
from sqlalchemy.orm import Session
from datetime import datetime

from modelsTables import Trade
from AppServices import MarketAnalyzer, NewsIntel, Notifier
from config import (
    TRADE_AMOUNT_USD, TAKE_PROFIT_PCT, STOP_LOSS_PCT, 
    MIN_AI_SCORE, MAX_OPEN_POSITIONS
)

class TradingBot:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.analyzer = MarketAnalyzer()
        self.news_intel = NewsIntel()

    def _is_asset_in_portfolio(self, symbol: str) -> bool:
        """Evita comprar lo que ya tenemos."""
        exists = self.db.query(Trade).filter(
            Trade.symbol == symbol.upper(), 
            Trade.status == "OPEN"
        ).first()
        return exists is not None

    def _count_open_positions(self) -> int:
        return self.db.query(Trade).filter(Trade.status == "OPEN").count()

    # ==========================================================
    # 🛡️ EL GUARDIÁN: Revisa precios y vende si toca SL/TP
    # ==========================================================
    def run_guardian_cycle(self):
        print(f"\n🛡️ [BOT GUARDIÁN] Vigilando posiciones: {datetime.now().strftime('%H:%M')}")
        open_trades = self.db.query(Trade).filter(Trade.status == "OPEN").all()
        
        if not open_trades:
            print("   💤 Cartera vacía. Nada que vigilar.")
            return

        for trade in open_trades:
            # 1. Precio en vivo
            current_price = self.analyzer.get_current_price(trade.symbol)
            if current_price <= 0:
                print(f"   ⚠️ Error precio {trade.symbol}. Saltando.")
                continue

            # 2. Cálculo P&L
            pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
            print(f"   👀 {trade.symbol}: ${current_price:.2f} ({pnl_pct:+.2f}%)")

            # 3. Decisiones
            sell_reason = None
            if pnl_pct >= TAKE_PROFIT_PCT:
                sell_reason = f"TAKE PROFIT (+{TAKE_PROFIT_PCT}%) 🚀"
            elif pnl_pct <= STOP_LOSS_PCT:
                sell_reason = f"STOP LOSS ({STOP_LOSS_PCT}%) 🛑"

            if sell_reason:
                self._execute_sell(trade, current_price, sell_reason, pnl_pct)

    def _execute_sell(self, trade: Trade, price: float, reason: str, pnl_pct: float):
        pnl_usd = (price - trade.entry_price) * trade.quantity
        
        trade.status = "CLOSED"
        trade.exit_price = price
        trade.sell_reason = reason
        trade.closed_at = datetime.utcnow()
        trade.realized_pnl = pnl_usd
        
        self.db.commit()
        
        icon = "🤑" if pnl_usd > 0 else "🩹"
        msg = (
            f"{icon} **BOT: VENTA EJECUTADA**\n"
            f"Activo: {trade.symbol}\n"
            f"Motivo: {reason}\n"
            f"PnL: {pnl_pct:.2f}% (${pnl_usd:.2f})"
        )
        Notifier.send_telegram_alert(msg)
        print(f"   ✅ Venta ejecutada: {trade.symbol}")

    # ==========================================================
    # 🏹 EL CAZADOR: Busca oportunidades y compra
    # ==========================================================
    def run_hunter_cycle(self, market_type='USA'):
        print(f"\n🏹 [BOT CAZADOR] Escaneando {market_type}...")
        
        if self._count_open_positions() >= MAX_OPEN_POSITIONS:
            print("   ⛔ Cupo lleno (Max Posiciones). No compro nada.")
            return

        # 1. Escaneo Técnico (CORREGIDO: Usando find_market_opportunities)
        # Ajustamos thresholds para ser exigentes
        opportunities = []
        if market_type == 'USA':
            opportunities = self.analyzer.find_market_opportunities('USA', threshold=-2.0, tier1_threshold=-1.5)
        elif market_type == 'MERVAL':
             opportunities = self.analyzer.find_market_opportunities('MERVAL', threshold=-2.0, tier1_threshold=-1.5)
        else:
             opportunities = self.analyzer.find_market_opportunities('CRYPTO', threshold=-3.0, tier1_threshold=-2.0)
        
        print(f"   🔎 Candidatos técnicos: {len(opportunities)}")

        for op in opportunities:
            symbol = op['symbol']
            
            # Filtro 1: ¿Ya la tengo?
            if self._is_asset_in_portfolio(symbol):
                continue

            # Filtro 2: Análisis IA
            print(f"   🧠 Analizando {symbol} con IA...")
            try:
                ai_analysis = self.news_intel.get_sentiment_analysis(
                    symbol=symbol, 
                    asset_name=op.get('name', ''), 
                    is_crypto=(market_type == 'CRYPTO'),
                    is_merval=(market_type == 'MERVAL')
                )
            except Exception as e:
                print(f"Error IA: {e}")
                continue
            
            decision = ai_analysis.get('decision', 'NEUTRAL')
            score = ai_analysis.get('score', 0)
            reason = ai_analysis.get('reason', 'Sin datos')

            print(f"      Resultado: {decision} (Score: {score})")

            # Filtro 3: Gatillo de Compra
            if decision == "BUY" and score >= MIN_AI_SCORE:
                # Guardamos SNAPSHOT para ML futuro
                snapshot = {
                    "rsi": op.get('rsi'),
                    "pct_change": op.get('percent_change') or op.get('percent_change_24h'),
                    "ai_score": score,
                    "market_type": market_type,
                    "ai_reason_summary": reason[:50]
                }
                
                self._execute_buy(symbol, op['price'], score, reason, snapshot)
                
                print("   ⏳ Enfriando motores tras compra (10s)...") # LOG NUEVO
                time.sleep(10) # <--- INTERVALO DE SEGURIDAD NUEVO
                
                # Chequear cupo nuevamente tras comprar
                if self._count_open_positions() >= MAX_OPEN_POSITIONS:
                    print("   ⛔ Cupo lleno tras compra.")
                    break
            
            # Pausa normal entre análisis (si no compró)
            time.sleep(2)

    def _execute_buy(self, symbol: str, price: float, score: int, reason: str, snapshot: dict):
        quantity = TRADE_AMOUNT_USD / price
        
        new_trade = Trade(
            symbol=symbol,
            entry_price=price,
            quantity=quantity,
            invested_amount=TRADE_AMOUNT_USD,
            status="OPEN",
            bought_at=datetime.utcnow(),
            analysis_snapshot=json.dumps(snapshot) # <--- DATA PARA ML
        )
        self.db.add(new_trade)
        self.db.commit()
        
        msg = (
            f"🔫 **BOT: COMPRA EJECUTADA**\n"
            f"Activo: {symbol}\n"
            f"Entrada: ${price:.2f}\n"
            f"IA Score: {score}\n"
            f"Tesis: {reason}"
        )
        Notifier.send_telegram_alert(msg)
        print(f"   ✅ Compra ejecutada: {symbol}")