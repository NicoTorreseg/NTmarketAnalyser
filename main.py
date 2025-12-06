# main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from database import engine, get_db, Base, SessionLocal, smart_migration
from modelsTables import CryptoSignal, StockSignal, Trade
from FieldsJSON import CoinSignalSchema, StockSignalSchema, TradeCreateSchema, PortfolioItemSchema
from AppServices import MarketAnalyzer, Notifier, NewsIntel
from config import SCHEDULE_HOURS

from fastapi import FastAPI, Depends, HTTPException, Request # <--- Agrega Request
from fastapi.responses import HTMLResponse # <--- Importante
from fastapi.templating import Jinja2Templates # <--- Importante
from datetime import timedelta # <--- Para filtrar por fecha

# --- LIFESPAN (Igual que antes) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 🚀 Iniciando Sistema ---")
    smart_migration(Base.metadata)
    Base.metadata.create_all(bind=engine)
    
    scheduler = BackgroundScheduler()
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(auto_check_market, 'cron', hour=hour, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()

def auto_check_market():
    """
    Escaneo Inteligente (Técnico + Fundamental/IA).
    """
    print(f"\n⏰ [AUTO] Escaneo Inteligente iniciado: {datetime.now()}")
    
    analyzer = MarketAnalyzer()
    news_intel = NewsIntel()
    db = SessionLocal()
    
    try:
        # --- A. ANÁLISIS TÉCNICO ---
        crypto_dips = analyzer.find_dip_opportunities(threshold=-5.0)
        stock_dips = analyzer.find_stock_dips(threshold=-3.0)
        merval_dips = analyzer.find_merval_dips(threshold=-2.0)
        
        valid_cryptos = []
        valid_stocks = [] # Preparado para stocks también

        # --- B. CRIPTO IA ---
        if crypto_dips:
            print(f"🔎 Analizando {len(crypto_dips)} candidatos cripto con IA...")
            for op in crypto_dips:
                # Consultar IA
                ai_analysis = news_intel.get_sentiment_analysis(op['symbol'], op['name'], is_crypto=True)
                
                decision = ai_analysis.get('decision', 'NEUTRAL')
                op['ai_score'] = ai_analysis.get('score', 50)
                op['ai_reason'] = ai_analysis.get('reason', 'Sin datos')
                op['ai_decision'] = decision

                print(f"   🤖 {op['symbol']}: {decision}")

                # FILTRO AUTOMÁTICO: Solo guardamos BUY o NEUTRAL (Ignoramos WAIT para no hacer spam)
                if decision in ["BUY", "NEUTRAL"]:
                    valid_cryptos.append(op)
                    
                    # Guardar en DB
                    db_signal = CryptoSignal(
                        symbol=op['symbol'], name=op['name'], 
                        price=op['price'], percent_change_24h=op['percent_change_24h'],
                        rsi=op['rsi'], ai_score=op['ai_score'],
                        ai_decision=decision, ai_reason=op['ai_reason']
                    )
                    db.add(db_signal)

        # --- C. STOCKS (Técnico por ahora, o IA simple) ---
        if stock_dips:
             for op in stock_dips:
                # Opcional: Agregar IA para stocks en auto aquí si quieres
                db_stock = StockSignal(
                    symbol=op['symbol'], price=op['price'], 
                    percent_change=op['percent_change'], rsi=op['rsi']
                )
                db.add(db_stock)
                # Convertimos a formato compatible para el reporte
                op['ai_decision'] = "TECNICO" 
                op['ai_score'] = 50
                op['ai_reason'] = "Detección automática por precio (Sin IA completa)"
                valid_stocks.append(op)
                
        if merval_dips:
             for op in merval_dips:
                # Lógica de guardado igual a stocks
                db_stock = StockSignal(
                    symbol=op['symbol'], price=op['price'], 
                    percent_change=op['percent_change'], rsi=op['rsi'],
                    ai_decision="TECNICO", ai_score=50, ai_reason="Auto Merval"
                )
                db.add(db_stock)
                op['ai_decision'] = "TECNICO"
                valid_stocks.append(op) # Lo agregamos a la lista para notificar junto con los otros stocks
        

        db.commit()

        # --- D. NOTIFICACIONES DETALLADAS 🔥 ---
        if valid_cryptos:
            msg = format_detailed_message("REPORTE AUTO CRIPTO", valid_cryptos)
            Notifier.send_telegram_alert(msg)
            
        if valid_stocks:
            msg = format_detailed_message("REPORTE AUTO STOCKS", valid_stocks)
            Notifier.send_telegram_alert(msg)
            
        if not valid_cryptos and not valid_stocks:
            print(">>> Sin oportunidades validadas.")

    except Exception as e:
        print(f"❌ Error Auto: {e}")
    finally:
        db.close()

app = FastAPI(title="Market Bot Trading & AI", lifespan=lifespan)
analyzer = MarketAnalyzer()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def root():
    return {"status": "Trading System Online 💸"}

# --- ENDPOINTS MANUALES ---

@app.get("/analyze", response_model=List[CoinSignalSchema])
def analyze_market(threshold: float = -5.0, db: Session = Depends(get_db)):
    return run_analysis_cycle(db, 'CRYPTO', threshold)

@app.get("/analyze/stocks", response_model=List[StockSignalSchema])
def analyze_stocks(threshold: float = -3.0, db: Session = Depends(get_db)):
    return run_analysis_cycle(db, 'USA', threshold)

@app.get("/analyze/Merval", response_model=List[StockSignalSchema])
def analyze_merval(threshold: float = -2.0, db: Session = Depends(get_db)):
    """
    Escanea ADRs Argentinos en Dólares (YPF, GGAL, MELI, etc.)
    Usa el motor unificado con el perfil 'MERVAL'.
    """
    # Toda la magia ocurre aquí dentro 👇
    return run_analysis_cycle(db, 'MERVAL', threshold)

# ==========================================
# --- NUEVOS ENDPOINTS: TRADING & SENTIMENT ---
# ==========================================

@app.get("/sentiment")
def get_sentiment():
    """Obtiene el Fear & Greed Index del mercado."""
    data = analyzer.get_market_sentiment()
    return {
        "status": "Success",
        "index_value": data.get("value"),
        "sentiment": data.get("value_classification"),
        "last_updated": datetime.now()
    }

@app.post("/trade/buy")
def execute_buy_order(order: TradeCreateSchema, db: Session = Depends(get_db)):
    """Simula una compra. Calcula cantidad basada en el precio actual."""
    # 1. Obtener precio actual real
    current_price = analyzer.get_current_price(order.symbol)
    
    if current_price <= 0:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener precio para {order.symbol}")
    
    # 2. Calcular cantidad
    quantity = order.investment_usd / current_price
    
    # 3. Guardar en DB
    new_trade = Trade(
        symbol=order.symbol.upper(),
        entry_price=current_price,
        quantity=quantity,
        invested_amount=order.investment_usd,
        status="OPEN"
    )
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    
    # 4. Notificar a Telegram
    msg = f"💸 **COMPRA EJECUTADA** 💸\nActivo: {new_trade.symbol}\nPrecio: ${round(current_price, 4)}\nInversión: ${order.investment_usd}\nCantidad: {round(quantity, 6)}"
    Notifier.send_telegram_alert(msg)
    
    return {"message": "Orden ejecutada", "trade_id": new_trade.id, "details": msg}

@app.get("/portfolio", response_model=List[PortfolioItemSchema])
def view_portfolio(db: Session = Depends(get_db)):
    """Ve tus posiciones abiertas y calcula Ganancia/Pérdida en tiempo real."""
    trades = db.query(Trade).filter(Trade.status == "OPEN").all()
    portfolio = []
    
    for trade in trades:
        # Precio actual en vivo
        live_price = analyzer.get_current_price(trade.symbol)
        
        # Si falla la API, usamos el precio de entrada para no romper el cálculo
        if live_price == 0:
            live_price = trade.entry_price 
            
        current_val = live_price * trade.quantity
        pnl = current_val - trade.invested_amount
        pnl_pct = (pnl / trade.invested_amount) * 100
        
        item = {
            "id": trade.id,
            "symbol": trade.symbol,
            "entry_price": trade.entry_price,
            "current_price": live_price,
            "quantity": trade.quantity,
            "invested_amount": trade.invested_amount,
            "current_value": current_val,
            "pnl_usd": round(pnl, 2),
            "pnl_percent": round(pnl_pct, 2),
            "bought_at": trade.bought_at
        }
        portfolio.append(item)
        
    return portfolio

# === NUEVO ENDPOINT PARA EL DASHBOARD ===
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
     Este endpoint sirve la interfaz gráfica. 
    
    # 🚀 [HAZ CLIC AQUÍ PARA ABRIR EL DASHBOARD](/dashboard)
    
    *(El botón 'Try it out' de abajo solo te mostrará el código HTML crudo)*
    """
  

    # 1. Recuperar últimos registros de ambas tablas
    recent_cryptos = db.query(CryptoSignal).order_by(CryptoSignal.detected_at.desc()).limit(20).all()
    recent_stocks = db.query(StockSignal).order_by(StockSignal.detected_at.desc()).limit(20).all()
    
    normalized_ops = []

    # 2. Normalizar Criptos (Mapear percent_change_24h -> percent_change)
    for c in recent_cryptos:
        normalized_ops.append({
            "symbol": c.symbol,
            "name": c.name,
            "price": c.price,
            "percent_change": c.percent_change_24h, # <--- AQUÍ ESTÁ EL FIX
            "rsi": c.rsi,
            "technical_signal": c.technical_signal,
            "ai_score": c.ai_score,
            "ai_decision": c.ai_decision,
            "ai_reason": c.ai_reason,
            "detected_at": c.detected_at
        })

    # 3. Normalizar Stocks (Ya tienen percent_change, pero unificamos estructura)
    for s in recent_stocks:
        normalized_ops.append({
            "symbol": s.symbol,
            "name": s.symbol, # Stocks no tienen campo 'name' en tu DB, usamos symbol
            "price": s.price,
            "percent_change": s.percent_change,
            "rsi": s.rsi,
            "technical_signal": s.technical_signal,
            "ai_score": s.ai_score,
            "ai_decision": s.ai_decision,
            "ai_reason": s.ai_reason,
            "detected_at": s.detected_at
        })

    # 4. Ordenar todo por fecha (lo más nuevo arriba)
    normalized_ops.sort(key=lambda x: x['detected_at'], reverse=True)

    # 5. Calcular datos del Portafolio (Paper Trading)
    portfolio_items = db.query(Trade).filter(Trade.status == "OPEN").all()
    total_invested = sum(item.invested_amount for item in portfolio_items)
    
    # Calculamos valor actual estimado (usando precio de entrada si no hay live price para no demorar)
    current_val_est = 0
    for item in portfolio_items:
        current_val_est += item.invested_amount # Simplificado para visualización rápida
        # Si quisieras PnL real en dashboard, habría que llamar a APIs, pero lo haría lento.
        # Mejor dejarlo estático o usar el precio de salida si existiera.

    total_pnl = current_val_est - total_invested # Dará 0 hasta que implementes live prices en dashboard

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "opportunities": normalized_ops, # <--- Ahora enviamos diccionarios limpios
        "portfolio": {
            "total_invested": total_invested,
            "current_value": current_val_est,
            "pnl": total_pnl,
            "pnl_percent": 0
        }
    })

# --- NUEVO ENDPOINT WEB DEL PORTAFOLIO ---
@app.get("/my-portfolio", response_class=HTMLResponse, tags=["Dashboard"])
def view_portfolio_web(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza el Portafolio Web (Solo Posiciones Abiertas).
    """
    trades = db.query(Trade).filter(Trade.status == "OPEN").all()
    portfolio_data = []
    
    for trade in trades:
        live_price = analyzer.get_current_price(trade.symbol)
        if live_price == 0: live_price = trade.entry_price 
            
        current_val = live_price * trade.quantity
        pnl = current_val - trade.invested_amount
        pnl_pct = (pnl / trade.invested_amount) * 100
        
        item = {
            "id": trade.id, # IDENTIFICADOR PARA EL BOTÓN DE VENTA
            "symbol": trade.symbol,
            "bought_at": trade.bought_at,
            "quantity": trade.quantity,
            "entry_price": trade.entry_price,
            "current_price": live_price,
            "current_value": current_val,
            "pnl_usd": pnl,
            "pnl_percent": pnl_pct
        }
        portfolio_data.append(item)
        
    return templates.TemplateResponse("portfolio.html", {
        "request": request, 
        "portfolio": portfolio_data
    })

# --- ENDPOINT DE VENTA MANUAL CORREGIDO ---
@app.post("/trade/sell/{trade_id}")
def manual_sell_trade(trade_id: int, db: Session = Depends(get_db)):
    """Venta Manual: Cierra la operación y guarda resultados."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade no encontrado")
    if trade.status == "CLOSED":
        raise HTTPException(status_code=400, detail="Este trade ya está cerrado")
        
    # 1. Obtener precio actual
    current_price = analyzer.get_current_price(trade.symbol)
    if current_price == 0: 
        # Si falla la API, usamos el precio de entrada como fallback de emergencia
        current_price = trade.entry_price 

    # 2. Calcular Ganancia
    pnl_usd = (current_price - trade.entry_price) * trade.quantity
    
    # 3. Actualizar TODOS los campos
    trade.status = "CLOSED"
    trade.exit_price = current_price
    trade.sell_reason = "MANUAL_SELL"
    trade.closed_at = datetime.utcnow()
    trade.realized_pnl = pnl_usd
    
    # 4. Guardar
    db.commit()
    
    # 5. Notificar
    icon = "💰" if pnl_usd > 0 else "📉"
    msg = (
        f"{icon} **VENTA MANUAL EJECUTADA**\n"
        f"Activo: {trade.symbol}\n"
        f"Salida: ${current_price:.4f}\n"
        f"PnL: ${pnl_usd:.2f}"
    )
    Notifier.send_telegram_alert(msg)
    
    return {"message": "Venta exitosa", "pnl": pnl_usd}

@app.get("/history", response_class=HTMLResponse, tags=["Dashboard"])
def view_history_web(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza el Historial de Trades Cerrados y el PnL Total.
    """
    # 1. Buscar trades cerrados ordenados por fecha de cierre descendente
    closed_trades = db.query(Trade)\
        .filter(Trade.status == "CLOSED")\
        .order_by(Trade.closed_at.desc())\
        .all()
    
    # 2. Calcular PnL Total Histórico
    total_pnl = sum(t.realized_pnl for t in closed_trades if t.realized_pnl is not None)
    
    # 3. Renderizar template
    return templates.TemplateResponse("history.html", {
        "request": request, 
        "trades": closed_trades,
        "total_pnl": total_pnl
    })

# --- HELPER: CONSTRUCTOR DE MENSAJES DETALLADOS ---
def format_detailed_message(title: str, signals: list):
    """
    Construye un mensaje de Telegram formateado con detalles de IA.
    Acepta tanto objetos de BD (SQLAlchemy) como diccionarios (Auto Scan).
    """
    if not signals:
        return None

    msg = f"🔔 **{title}** 🔔\n\n"
    
    for item in signals:
        # Detectar si es diccionario (Auto) u Objeto DB (Manual)
        is_dict = isinstance(item, dict)
        
        symbol = item['symbol'] if is_dict else item.symbol
        price = item['price'] if is_dict else item.price
        pct = item['percent_change_24h'] if is_dict else (item.percent_change if hasattr(item, 'percent_change') else item.percent_change_24h)
        decision = item.get('ai_decision', 'N/A') if is_dict else item.ai_decision
        score = item.get('ai_score', 0) if is_dict else item.ai_score
        reason = item.get('ai_reason', 'Sin datos') if is_dict else item.ai_reason

        # Emojis según decisión
        icon = "✅" if decision == "BUY" else ("⚠️" if decision == "WAIT" else "😐")
        
        msg += f"{icon} **{symbol}** ({pct:.2f}%)\n"
        msg += f"💲 Precio: ${price:.4f}\n"
        msg += f"🧠 IA: **{decision}** (Score: {score})\n"
        msg += f"📝 _Opinion: {reason}_\n"
        msg += "---------------------------\n"
    
    return msg

def run_analysis_cycle(db: Session, market_type: str, threshold: float):
    news_intel = NewsIntel()
    
    # 1. Usamos el nuevo Escáner Universal
    opportunities = analyzer.find_market_opportunities(market_type, threshold)
    saved_signals = []
    
    msg_inicio = f"🔎 Iniciando Análisis {market_type} ({len(opportunities)} activos)..."
    print(msg_inicio)
    Notifier.send_telegram_alert(msg_inicio)

    for op in opportunities:
        # 2. Análisis IA (Lógica Unificada)
        # Determinamos si es crypto o merval para el contexto de la noticia
        is_crypto = (market_type == 'CRYPTO')
        is_merval = (market_type == 'MERVAL')
        
        try:
            ai_analysis = news_intel.get_sentiment_analysis(
                symbol=op['symbol'], 
                asset_name=op['name'], 
                is_crypto=is_crypto,
                is_merval=is_merval
            )
        except:
            ai_analysis = {"score": 50, "decision": "NEUTRAL", "reason": "Error IA"}

        # 3. Guardado Polimórfico (Aquí el único IF necesario)
        if market_type == 'CRYPTO':
            db_signal = CryptoSignal(
                symbol=op['symbol'], name=op['name'], 
                price=op['price'], percent_change_24h=op['percent_change'], # Ojo: unificamos a percent_change en el scanner
                rsi=op['rsi'], technical_signal=op['technical_signal'],
                ai_score=ai_analysis.get('score'), ai_decision=ai_analysis.get('decision'), ai_reason=ai_analysis.get('reason')
            )
        else:
            # Stock y Merval usan la misma tabla StockSignal
            db_signal = StockSignal(
                symbol=op['symbol'], 
                price=op['price'], percent_change=op['percent_change'],
                rsi=op['rsi'], technical_signal=op['technical_signal'],
                ai_score=ai_analysis.get('score'), ai_decision=ai_analysis.get('decision'), ai_reason=ai_analysis.get('reason')
            )
            
        db.add(db_signal)
        saved_signals.append(db_signal) # Guardamos para el reporte
    
    db.commit()
    
    # 4. Reporte Unificado
    if saved_signals:
        full_msg = format_detailed_message(f"REPORTE {market_type}", saved_signals)
        Notifier.send_telegram_alert(full_msg)
    
    return saved_signals
# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    hostsv="127.0.0.1" #local es "127.0.0.1"
    print("--- Iniciando servidor modular ---")
    print(f"Documentación disponible en: http://{hostsv}:8000/docs")
    print(f"Cliente: http://192.168.0.50:8000/docs")
    uvicorn.run(app, host=hostsv, port=8000)