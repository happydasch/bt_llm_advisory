import backtrader as bt
import numpy as np

from llm_advisory.pydantic_models import (
    LLMAdvisorDataArtefact,
    LLMAdvisorUpdateStateData,
)
from llm_advisory.helper.llm_prompt import compile_data_artefacts

from bt_llm_advisory import BacktraderLLMAdvisor
from bt_llm_advisory.helper.bt_data_generation import get_data_feed_name


ADVISOR_INSTRUCTIONS = """
You are an Backtrader Reversal Advisor, an AI advisor agent specialized in detecting
reversal in trends from indicator values and close prices.
You operate as one advisor within a multi-agent advisory system; your sole
responsibility is to analyze all provided DataFeeds and output 1 of 4 trend signals.
If unsure or unable to identify current trend, use "none" as a signal.
When you receive more than one DataFeed use the additonal DataFeeds for confirmation
of the reversal.

---

DATA FORMAT
You will receive data with the following fields:
    - price_history: [float,…]        # last n closing prices
    - ma_short: float                 # short-period moving average
    - ma_long: float                  # long-period moving average
    - ma_diff: float                  # ma_short - ma_long
    - adx: float                      # Average Directional Index
    - atr: float                      # Average True Range
    - rsi: float                      # Relative Strength Index
    - bb_width: float                 # Bollinger Band width
    - linreg_slope: float             # slope of linear regression

---

TASK
1. Return exactly one of:
    - "bullish"   — when there is a clear bullish reversal in trend
    - "bearish"   — when there is a clear bearish reversal in trend
    - "neutral"   — when the market is range-bound and the price oscillates
    - "none"      — insufficient or conflicting data to call a reversal
2. Describe your signals in reasoning
3. Assign a confidence score between 0.0 and 1.0 reflecting your conviction
in the selected reversal where 0.0 is the lowest conviction and 1.0 is the highest
conviction matching the reasoning

---

IMPORTANT CONSTRAINS
    - Do not emit more than one signal.
    - Do not invent data or signals — your response must be directly supported by the latest available data.
    - Your signal is used to guide the next trade decision immediately after the current data.

---"""


class BollingerBandsW(bt.ind.BollingerBands):
    """
    Extends the Bollinger Bands with a Percentage line
    """

    alias = ("BBW",)
    lines = ("bbw",)
    plotlines = dict(
        top=dict(_plotskip=True),
        mid=dict(_plotskip=True),
        bot=dict(_plotskip=True),
        bbw=dict(_name="bbw", color="green", _skipnan=True),
    )
    plotinfo = dict(subplot=True)

    def __init__(self):
        super(BollingerBandsW, self).__init__()
        self.l.bbw = (self.l.top - self.l.bot) / self.l.mid


class LinearRegressionSlope(bt.Indicator):
    """
    Computes the slope of a linear regression over the last `period` values of `data`.
    """

    lines = ("slope",)
    params = (("period", 10),)  # look‐back window

    def __init__(self):
        # ensure we have at least `period` data points before calculating
        self.addminperiod(self.params.period)

    def next(self):
        # grab the last `period` values as a NumPy array
        y = np.array(self.data.get(size=self.params.period))
        x = np.arange(self.params.period)
        # compute slope = Cov(x,y) / Var(x)
        xm = x.mean()
        ym = y.mean()
        slope = ((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum()
        self.lines.slope[0] = slope


class BacktraderReversalAdvisor(BacktraderLLMAdvisor):

    advisor_instructions = ADVISOR_INSTRUCTIONS

    def __init__(
        self,
        short_ma_period: int = 10,  # period for short moving average
        long_ma_period: int = 50,  # period for long moving average
        lookback_period: int = 5,  # lookback period for trend data
        add_all_data_feeds: bool = False,  # adds all data if True, only first if False
    ):
        super().__init__()
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.lookback_period = lookback_period
        self.add_all_data_feeds = add_all_data_feeds
        self.indicators: dict[str, dict[str, bt.Indicator]] = {}

    def init_strategy(self, strategy):
        # init and add all required indicators
        data_feeds = (
            [strategy.datas[0]] if not self.add_all_data_feeds else strategy.datas
        )
        for data_feed in data_feeds:
            short_ma = bt.ind.SMA(
                data_feed,
                period=self.short_ma_period,
                # plotskip=True,
                plotname="bt_reversal_short_ma",
            )
            long_ma = bt.ind.SMA(
                data_feed,
                period=self.long_ma_period,
                plotskip=True,
                plotname="bt_reversal_long_ma",
            )
            adx = bt.ind.AverageDirectionalMovementIndex(
                data_feed,
                plotskip=True,
                plotname="bt_reversal_adx",
            )
            atr = bt.ind.ATR(
                data_feed,
                plotskip=True,
                plotname="bt_reversal_atr",
            )
            rsi = bt.ind.RSI(
                data_feed,
                plotskip=True,
                plotname="bt_reversal_rsi",
            )
            bb = BollingerBandsW(
                data_feed,
                plotskip=True,
                plotname="bt_reversal_bb",
            )
            linreg_slope = LinearRegressionSlope(
                data_feed,
                plotskip=True,
                period=10,
            )
            data_indicators = {
                "short_ma": short_ma,
                "long_ma": long_ma,
                "ma_diff": long_ma - short_ma,
                "adx": adx,
                "atr": atr,
                "rsi": rsi,
                "bb_width": bb.bbw,
                "linreg_slope": linreg_slope,
            }
            self.indicators[data_feed] = data_indicators

    def update_state(
        self, state: LLMAdvisorUpdateStateData
    ) -> LLMAdvisorUpdateStateData:
        self.advisor_messages_input.advisor_prompt = state.messages[0].content
        self.advisor_messages_input.advisor_data = compile_data_artefacts(
            self._get_trend_indicators_data(self.lookback_period)
        )
        return self._update_state(state)

    def _get_trend_indicators_data(
        self, lookback_period: int, accuracy: int = 4
    ) -> LLMAdvisorDataArtefact:
        response = []
        for data_feed, indicators in self.indicators.items():
            feed_data = {
                "price_history": [data_feed[-i] for i in range(lookback_period)]
            }
            feed_data |= {
                indicator_name: round(indicator[0], accuracy)
                for indicator_name, indicator in indicators.items()
            }
            response.append(
                LLMAdvisorDataArtefact(
                    description=f"DataFeed {get_data_feed_name(data_feed)}",
                    artefact=feed_data,
                )
            )
        return response
