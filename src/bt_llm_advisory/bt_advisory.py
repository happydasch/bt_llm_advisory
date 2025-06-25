from backtrader import Strategy

from llm_advisory.llm_advisory import LLMAdvisory

from bt_llm_advisory import BacktraderLLMAdvisor
from bt_llm_advisory.state_advisors import BacktraderAdvisoryAdvisor

DATA_LOOKBACK_PERIOD = 25
INDICATOR_LOOKBACK_PERIOD = 10


class BacktraderLLMAdvisory(LLMAdvisory):
    """LLM Advisory for backtrader"""

    def init_strategy(
        self,
        strategy: Strategy,
        data_lookback_period: int = DATA_LOOKBACK_PERIOD,
        indicator_lookback_period=INDICATOR_LOOKBACK_PERIOD,
    ) -> None:
        """Initializes backtrader functionality

        This method needs to be called inside __init__ of the strategy it is running on
        ```
        class Strategy(bt.Strategy):

            def __init__(self):
                self.bt_llm_advisory = BacktraderLLMAdvisory(...)
                self.bt_llm_advisory.init_strategy(self)
        ```
        """
        self.advisory_advisor = BacktraderAdvisoryAdvisor()
        self.metadata["strategy"] = strategy
        self.metadata["data_lookback_period"] = data_lookback_period
        self.metadata["indicator_lookback_period"] = indicator_lookback_period
        for advisor in self.all_advisors + [self.advisory_advisor]:
            if not isinstance(advisor, BacktraderLLMAdvisor):
                continue
            if not hasattr(advisor, "init_strategy"):
                continue
            advisor.init_strategy(strategy)
