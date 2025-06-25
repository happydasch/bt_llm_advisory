from backtrader import Observer


class LLMAdvisoryObserver(Observer):

    lines = (
        "buy",
        "sell",
        "close",
        "none",
    )

    plotinfo = dict(
        plot=True,
        subplot=False,
        plotvaluetags=False,
        plotlinevalues=True,
        plotabove=True,
        plotname="Advisories",
    )
    plotlines = dict(
        buy=dict(
            marker="$B$",
            markersize=7.0,
            color="green",
            ls="",
        ),
        sell=dict(
            marker="$S$",
            markersize=7.0,
            color="red",
            ls="",
        ),
        close=dict(
            marker="$C$",
            markersize=7.0,
            color="blue",
            ls="",
        ),
        none=dict(
            marker="$-$",
            markersize=7.0,
            color="gray",
            ls="",
        ),
    )

    def __init__(self, advisories: list):
        self.advisories: list = advisories

    def next(self):
        if not len(self.advisories):
            return
        advisory = self.advisories.pop(0)
        signal = advisory.signal
        if signal == "buy":
            self.l.buy[0] = self.data.close[0]
        elif signal == "sell":
            self.l.sell[0] = self.data.close[0]
        elif signal == "close":
            self.l.close[0] = self.data.close[0]
        elif signal == "none":
            self.l.none[0] = self.data.close[0]
