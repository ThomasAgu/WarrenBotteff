import os
import time
from datetime import datetime

import ccxt
import pandas as pd
import pandas_ta as ta

from evaluator import StrategyEvaluator
from reporter import TradeReporter
from strategies.ema_rsi import EMARSIStrategy
from trade import Trade


API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL_USDT", 1000))
POSITION_SIZE = float(os.getenv("POSITION_SIZE_USDT", 50))
FEE_RESERVE_RATE = float(os.getenv("FEE_RESERVE_RATE", 0.001))

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": SECRET_KEY,
    "enableRateLimit": True,
    "options": {"defaultType": "spot"}
})

if USE_TESTNET:
    exchange.set_sandbox_mode(True)
    print("Modo: TESTNET (Dinero Simulado)")
else:
    print("Modo: CUENTA REAL")


def get_market_data(symbol, timeframe, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["EMA_fast"] = ta.ema(df["close"], length=20)
    df["EMA_slow"] = ta.ema(df["close"], length=50)
    df["RSI"] = ta.rsi(df["close"], length=14)
    return df


def order_fee(order):
    fee_items = order.get("fees")
    if fee_items is None:
        fee = order.get("fee")
        fee_items = [fee] if fee else []
    return sum(float(item.get("cost") or 0) for item in fee_items if item)


def execution_details(order, fallback_price, fallback_quantity):
    price = float(order.get("average") or order.get("price") or fallback_price)
    quantity = float(order.get("filled") or fallback_quantity)
    return price, quantity, order_fee(order)


def print_account_balance(exchange_client):
    balance = exchange_client.fetch_balance()
    assets = []
    for asset, total in balance.get("total", {}).items():
        total = float(total or 0.0)
        if total == 0:
            continue
        free = float(balance.get("free", {}).get(asset, 0.0) or 0.0)
        used = float(balance.get("used", {}).get(asset, 0.0) or 0.0)
        assets.append(f"{asset}: libre={free:.8f}, bloqueado={used:.8f}, total={total:.8f}")

    print("Balance Spot:")
    if assets:
        for asset in assets:
            print(f"  {asset}")
    else:
        print("  No hay activos con saldo.")


class TradingEngine:
    def __init__(self, exchange_client, symbol, position_size, evaluator, reporter, strategy):
        self.exchange = exchange_client
        self.symbol = symbol
        self.position_size = position_size
        self.evaluator = evaluator
        self.reporter = reporter
        self.strategy = strategy
        self.position = None

    def _balance_equity(self, current_price):
        balance = self.exchange.fetch_balance()
        quote, base = self.symbol.split("/")
        quote_free = float(balance["free"].get(quote, 0.0))
        base_free = float(balance["free"].get(base, 0.0))
        return quote_free + base_free * current_price

    def _buy(self, current_price):
        balance = self.exchange.fetch_balance()
        quote = self.symbol.split("/")[1]
        quote_free = float(balance["free"].get(quote, 0.0))
        required_quote = self.position_size * (1 + FEE_RESERVE_RATE)
        if quote_free < required_quote:
            missing_quote = required_quote - quote_free
            print(
                f"Saldo insuficiente en {quote}: disponible ${quote_free:.2f}; "
                f"necesario aproximadamente ${required_quote:.2f} "
                f"(faltan ${missing_quote:.2f}) para una posición de ${self.position_size:.2f}."
            )
            return

        requested_quantity = self.exchange.amount_to_precision(
            self.symbol, self.position_size / current_price
        )
        order = self.exchange.create_market_buy_order(self.symbol, requested_quantity)
        entry_price, quantity, fee = execution_details(order, current_price, requested_quantity)
        entry_time = datetime.fromtimestamp(order["timestamp"] / 1000) if order.get("timestamp") else datetime.now()
        self.position = {"entry_time": entry_time, "entry_price": entry_price, "quantity": quantity, "fee": fee}
        print(f"COMPRA ejecutada: {order['id']}")

    def _sell(self, current_price):
        position = self.position
        order = self.exchange.create_market_sell_order(self.symbol, position["quantity"])
        exit_price, sold_quantity, exit_fee = execution_details(order, current_price, position["quantity"])
        quantity = min(position["quantity"], sold_quantity)
        exit_time = datetime.fromtimestamp(order["timestamp"] / 1000) if order.get("timestamp") else datetime.now()
        trade = Trade(self.symbol, position["entry_time"], exit_time, position["entry_price"], exit_price, quantity, (exit_price - position["entry_price"]) * quantity, position["fee"] + exit_fee)
        self.evaluator.add_trade(trade)
        print(f"VENTA ejecutada: {order['id']}")
        self.position = None

    def run_cycle(self):
        df = get_market_data(self.symbol, TIMEFRAME)
        last_candle = df.iloc[-2]
        current_price = float(df.iloc[-1]["close"])
        timestamp = datetime.now()
        self.evaluator.add_equity_point(timestamp, self._balance_equity(current_price))
        print(f"[{timestamp:%Y-%m-%d %H:%M:%S}] Precio: ${current_price:.2f}")
        if self.position is None and self.strategy.should_buy(last_candle):
            self._buy(current_price)
        elif self.position is not None and self.strategy.should_sell(last_candle):
            self._sell(current_price)
        metrics = self.evaluator.calculate()
        print(f"Trades: {metrics['total_trades']} | Win Rate: {metrics['win_rate']:.2f}% | Net Profit: ${metrics['net_profit']:.2f} | Return: {metrics['return_percentage']:.2f}% | Profit Factor: {metrics['profit_factor']:.2f} | Max Drawdown: {metrics['max_drawdown_percentage']:.2f}%")
        self.reporter.generate_report(self.evaluator.trades, metrics, self.evaluator.equity_curve, self.strategy.name)


def run_bot():
    strategy = EMARSIStrategy()
    evaluator = StrategyEvaluator(INITIAL_CAPITAL)
    engine = TradingEngine(exchange, SYMBOL, POSITION_SIZE, evaluator, TradeReporter(), strategy)
    print(f"Bot iniciado para {SYMBOL} [{TIMEFRAME}]")

    print(f"Strategy: {strategy.name}")
    print(f"Initial Capital: ${INITIAL_CAPITAL:.2f}")
    print(f"Position Size: ${POSITION_SIZE:.2f}")
    print_account_balance(exchange)
    while True:
        try:
            engine.run_cycle()
            time.sleep(60)
        except Exception as error:
            print(f"Error: {error}")
            time.sleep(30)


if __name__ == "__main__":
    run_bot()
