class EMARSIStrategy:
    name = "EMA_RSI"

    def should_buy(self, candle) -> bool:
        return candle["EMA_fast"] > candle["EMA_slow"] and candle["RSI"] < 70

    def should_sell(self, candle) -> bool:
        return candle["EMA_fast"] < candle["EMA_slow"] or candle["RSI"] > 75
