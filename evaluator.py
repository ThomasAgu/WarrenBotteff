import math
from datetime import datetime
from typing import Optional

from trade import Trade


class StrategyEvaluator:
    def __init__(self, initial_balance: float):
        self.initial_balance = float(initial_balance)
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple[datetime, float]] = []

    def add_trade(self, trade: Trade) -> None:
        self.trades.append(trade)

    def add_equity_point(self, timestamp: datetime, balance: float) -> None:
        self.equity_curve.append((timestamp, float(balance)))

    @staticmethod
    def _average(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def _drawdown_metrics(self) -> tuple[float, float]:
        peak = self.initial_balance
        max_drawdown = 0.0
        max_drawdown_percentage = 0.0
        for _, equity in self.equity_curve:
            peak = max(peak, equity)
            drawdown = equity - peak
            drawdown_percentage = drawdown / peak * 100 if peak else 0.0
            max_drawdown = min(max_drawdown, drawdown)
            max_drawdown_percentage = min(max_drawdown_percentage, drawdown_percentage)
        return max_drawdown, max_drawdown_percentage

    def _equity_returns(self) -> list[float]:
        points = sorted(self.equity_curve, key=lambda point: point[0])
        returns = []
        for (_, previous), (_, current) in zip(points, points[1:]):
            if previous != 0:
                returns.append((current - previous) / previous)
        return returns

    def _ratios(self) -> tuple[float, float]:
        returns = self._equity_returns()
        if len(returns) < 2:
            return 0.0, 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
        standard_deviation = math.sqrt(variance)
        # Sharpe compares average equity return with its total volatility.
        sharpe = mean_return / standard_deviation if standard_deviation else 0.0

        negative_returns = [value for value in returns if value < 0]
        downside_deviation = math.sqrt(
            sum(value ** 2 for value in negative_returns) / len(negative_returns)
        ) if negative_returns else 0.0
        # Sortino uses only downside volatility, so it isolates harmful variation.
        sortino = mean_return / downside_deviation if downside_deviation else 0.0
        return sharpe, sortino

    def calculate(self) -> dict:
        net_pnls = [trade.net_pnl for trade in self.trades]
        winning_pnls = [pnl for pnl in net_pnls if pnl > 0]
        losing_pnls = [pnl for pnl in net_pnls if pnl < 0]
        total_trades = len(self.trades)
        net_profit = sum(net_pnls)
        gross_profit = sum(winning_pnls)
        gross_loss = abs(sum(losing_pnls))
        max_drawdown, max_drawdown_percentage = self._drawdown_metrics()
        sharpe_ratio, sortino_ratio = self._ratios()

        timestamps = [point[0] for point in self.equity_curve]
        timestamps.extend(time for trade in self.trades for time in (trade.entry_time, trade.exit_time))
        start_time: Optional[datetime] = min(timestamps) if timestamps else None
        end_time: Optional[datetime] = max(timestamps) if timestamps else None

        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.initial_balance + net_profit,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "net_profit": net_profit,
            "return_percentage": net_profit / self.initial_balance * 100 if self.initial_balance else 0.0,
            "total_trades": total_trades,
            "winning_trades": len(winning_pnls),
            "losing_trades": len(losing_pnls),
            "win_rate": len(winning_pnls) / total_trades * 100 if total_trades else 0.0,
            "profit_factor": gross_profit / gross_loss if gross_loss else 0.0,
            "total_fees": sum(trade.fees for trade in self.trades),
            "average_trade": net_profit / total_trades if total_trades else 0.0,
            "average_win": self._average(winning_pnls),
            "average_loss": abs(self._average(losing_pnls)),
            "average_trade_duration_seconds": self._average([trade.duration_seconds for trade in self.trades]),
            "max_drawdown": max_drawdown,
            "max_drawdown_percentage": max_drawdown_percentage,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": (end_time - start_time).total_seconds() if start_time and end_time else 0.0,
        }
