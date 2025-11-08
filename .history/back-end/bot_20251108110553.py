# ------------------------------------------------------------
# BOT BASE CLASS
# ------------------------------------------------------------
class Bot:
    def __init__(self, name, wallet, market):
        self.name = name
        self.wallet = wallet
        self.market = market
        self.last_action = None

    def step(self):
        raise NotImplementedError


# ------------------------------------------------------------
# BOT STRATEGIES
# ------------------------------------------------------------

class RandomTrader(Bot):
    """Trades randomly to stay active."""
    def step(self):
        action = random.choice(["buy", "sell", "hold"])
        amount = random.uniform(0.5, 2)
        price = self.market.price
        if action == "buy":
            self.wallet.trade(amount, price)
        elif action == "sell":
            self.wallet.trade(-amount, price)
        self.last_action = action


class MomentumBot(Bot):
    """Buys when short-term trend exceeds long-term trend."""
    def step(self):
        short_ma = self.market.moving_average(5)
        long_ma = self.market.moving_average(20)
        price = self.market.price
        amount = 1

        if short_ma > long_ma:
            self.wallet.trade(amount, price)
            self.last_action = "buy"
        elif short_ma < long_ma:
            self.wallet.trade(-amount, price)
            self.last_action = "sell"
        else:
            self.last_action = "hold"


class MeanReverter(Bot):
    """Sells when price deviates from mean, buys when below."""
    def step(self):
        mean = self.market.moving_average(15)
        price = self.market.price
        threshold = 0.02 * mean
        amount = 1

        if price > mean + threshold:
            self.wallet.trade(-amount, price)
            self.last_action = "sell"
        elif price < mean - threshold:
            self.wallet.trade(amount, price)
            self.last_action = "buy"
        else:
            self.last_action = "hold"


class MarketMaker(Bot):
    """Places bid/ask around mid, simulating liquidity."""
    def __init__(self, name, wallet, market):
        super().__init__(name, wallet, market)
        self.spread = 0.01

    def step(self):
        vol = self.market.volatility()
        price = self.market.price
        bid = price * (1 - self.spread - vol)
        ask = price * (1 + self.spread + vol)
        amount = 0.5

        # If price drifts up, sell some; if down, buy some
        if random.random() < 0.5:
            self.wallet.trade(amount, ask)
            self.last_action = "sell (ask)"
        else:
            self.wallet.trade(-amount, bid)
            self.last_action = "buy (bid)"


class Hedger(Bot):
    """Maintains balanced exposure by adjusting for volatility."""
    def step(self):
        price = self.market.price
        vol = self.market.volatility()
        target_bc = 100 / (1 + 50 * vol)
        delta = target_bc - self.wallet.bc
        if abs(delta) > 1:
            self.wallet.trade(delta * 0.1, price)
            self.last_action = "adjust exposure"
        else:
            self.last_action = "hold"
