import os
import time
import ccxt
import pandas as pd
import pandas_ta as ta

from reporter import TradeReporter

# Lectura de variables de entorno
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
USE_TESTNET = os.getenv('USE_TESTNET', 'true').lower() == 'true'
SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
TIMEFRAME = os.getenv('TIMEFRAME', '1h')
AMOUNT_USDT = float(os.getenv('AMOUNT_USDT', 50))


# Inicializacion 

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

if USE_TESTNET:
    exchange.set_sandbox_mode(True)
    print("⚠️  Modo: TESTNET (Dinero Simulado)")
else:
    print("🔴 Modo: CUENTA REAL")

# Modulo de reporte
reporter = TradeReporter(capital_inicial=AMOUNT_USDT)


def get_market_data(symbol, timeframe, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    df['EMA_fast'] = ta.ema(df['close'], length=20)
    df['EMA_slow'] = ta.ema(df['close'], length=50)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def run_bot():
    print(f"Bot iniciado para {SYMBOL} [{TIMEFRAME}]...")
    in_position = False
    buy_cost = 0.0

    #Para ver si esta actualizando el reporte
    reporter.log_trade(
                        tipo="COMPRA",
                        moneda=SYMBOL,
                        cantidad=20,
                        valor_usd=20,
                        pnl=0.0
                    )
    while True:
        try:
            df = get_market_data(SYMBOL, TIMEFRAME)
            last_candle = df.iloc[-2]
            current_price = df.iloc[-1]['close']

            buy_condition = (last_candle['EMA_fast'] > last_candle['EMA_slow']) and (last_candle['RSI'] < 70)
            sell_condition = (last_candle['EMA_fast'] < last_candle['EMA_slow']) or (last_candle['RSI'] > 75)

            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Precio: ${current_price:.2f} | EMA_F: {last_candle['EMA_fast']:.2f} | EMA_S: {last_candle['EMA_slow']:.2f} | RSI: {last_candle['RSI']:.2f}")

            if buy_condition and not in_position:
                # 1. Obtener saldo disponible en USDT
                balance = exchange.fetch_balance()
                usdt_free = balance['free'].get('USDT', 0.0)

                # 2. Usar el monto deseado o el total disponible si tienes menos
                usdt_to_spend = min(AMOUNT_USDT, usdt_free * 0.99) # 0.99 para dejar un margen por comisiones

                if usdt_to_spend >= 10:  # Mínimo de compra en Binance (~$10)
                    amount_to_buy = usdt_to_spend / current_price
                    order = exchange.create_market_buy_order(SYMBOL, amount_to_buy)
                    print(f"🚀 COMPRA ejecutada: {order['id']}")
                    buy_cost = amount_to_buy * current_price
                    reporter.log_trade(
                        tipo="COMPRA",
                        moneda=SYMBOL,
                        cantidad=amount_to_buy,
                        valor_usd=buy_cost,
                        pnl=0.0
                    )
                    in_position = True
                else:
                    print(f"⚠️ Saldo insuficiente en USDT (${usdt_free:.2f}) para abrir posición.")

            elif sell_condition and in_position:
                balance = exchange.fetch_balance()
                base_currency = SYMBOL.split('/')[0]
                btc_balance = balance['free'].get(base_currency, 0.0)
                sell_value = btc_balance * current_price
                pnl = sell_value - buy_cost 
                
                order = exchange.create_market_sell_order(SYMBOL, btc_balance)
                print(f"🔻 VENTA ejecutada: {order['id']}")
                reporter.log_trade(
                    tipo="VENTA",
                    moneda=SYMBOL,
                    cantidad=btc_balance,
                    valor_usd=sell_value,
                    pnl=pnl
                )
                in_position = False
                buy_cost = 0.0

            time.sleep(60)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(30)

if __name__ == '__main__':
    run_bot()