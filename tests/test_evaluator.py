from datetime import datetime, timedelta

import pytest

from evaluator import StrategyEvaluator
from trade import Trade


START = datetime(2026, 1, 1, 10, 0, 0)


def make_trade(pnl, fees=0.0, offset=0, duration=60):
    entry = START + timedelta(minutes=offset)
    exit_time = entry + timedelta(seconds=duration)
    entry_price = 100.0
    quantity = 1.0
    gross_pnl = pnl + fees
    exit_price = entry_price + gross_pnl
    return Trade("BTC/USDT", entry, exit_time, entry_price, exit_price, quantity, gross_pnl, fees)


def test_no_trades():
    metrics = StrategyEvaluator(1000).calculate()
    assert metrics["total_trades"] == 0
    assert metrics["final_balance"] == 1000
    assert metrics["win_rate"] == 0
    assert metrics["sharpe_ratio"] == 0
    assert metrics["sortino_ratio"] == 0


def test_mixed_trades_metrics_and_fees():
    evaluator = StrategyEvaluator(1000)
    for pnl in (100, -50, 50, -25):
        evaluator.add_trade(make_trade(pnl, fees=1))

    metrics = evaluator.calculate()
    assert metrics["net_profit"] == pytest.approx(75)
    assert metrics["final_balance"] == pytest.approx(1075)
    assert metrics["total_trades"] == 4
    assert metrics["winning_trades"] == 2
    assert metrics["losing_trades"] == 2
    assert metrics["win_rate"] == pytest.approx(50)
    assert metrics["gross_profit"] == pytest.approx(150)
    assert metrics["gross_loss"] == pytest.approx(75)
    assert metrics["profit_factor"] == pytest.approx(2)
    assert metrics["total_fees"] == pytest.approx(4)
    assert metrics["return_percentage"] == pytest.approx(7.5)


def test_all_winners_and_no_gross_loss():
    evaluator = StrategyEvaluator(1000)
    evaluator.add_trade(make_trade(10))
    evaluator.add_trade(make_trade(20, offset=1))
    metrics = evaluator.calculate()
    assert metrics["average_win"] == pytest.approx(15)
    assert metrics["average_loss"] == 0
    assert metrics["profit_factor"] == 0


def test_all_losers_and_average_duration():
    evaluator = StrategyEvaluator(1000)
    evaluator.add_trade(make_trade(-10, duration=30))
    evaluator.add_trade(make_trade(-20, offset=1, duration=90))
    metrics = evaluator.calculate()
    assert metrics["average_loss"] == pytest.approx(15)
    assert metrics["average_trade_duration_seconds"] == pytest.approx(60)


def test_equity_curve_drawdown_and_ratios():
    evaluator = StrategyEvaluator(1000)
    for index, equity in enumerate((1000, 1050, 1100, 1000, 900, 950)):
        evaluator.add_equity_point(START + timedelta(hours=index), equity)
    metrics = evaluator.calculate()
    assert metrics["max_drawdown"] == pytest.approx(-200)
    assert metrics["max_drawdown_percentage"] == pytest.approx(-200 / 1100 * 100)
    assert metrics["sharpe_ratio"] != 0
    assert metrics["sortino_ratio"] != 0


def test_few_equity_points_do_not_break_ratios():
    evaluator = StrategyEvaluator(1000)
    evaluator.add_equity_point(START, 1000)
    evaluator.add_equity_point(START + timedelta(hours=1), 1010)
    metrics = evaluator.calculate()
    assert metrics["sharpe_ratio"] == 0
    assert metrics["sortino_ratio"] == 0
