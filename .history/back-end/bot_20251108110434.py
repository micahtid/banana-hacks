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