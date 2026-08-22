from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees: float = 0.0

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.fees

    @property
    def duration_seconds(self) -> float:
        return (self.exit_time - self.entry_time).total_seconds()

    @property
    def return_percentage(self) -> float:
        capital_used = self.entry_price * self.quantity
        if capital_used == 0:
            return 0.0
        return self.net_pnl / capital_used * 100
