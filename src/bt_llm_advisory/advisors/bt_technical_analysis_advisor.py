from llm_advisory.pydantic_models import (
    LLMAdvisorState,
    LLMAdvisorDataArtefact,
    LLMAdvisorDataArtefactOutputMode,
    LLMAdvisorUpdateStateData,
)
from llm_advisory.helper.llm_prompt import compile_data_artefacts

from bt_llm_advisory import BacktraderLLMAdvisor
from bt_llm_advisory.helper.bt_data_generation import (
    get_data_feed_name,
    get_strategy_from_state,
    generate_data_feed_data,
    get_indicator_name,
    show_lineroot_obj,
    generate_indicator_data,
)


ADVISOR_INSTRUCTIONS = """"
You are the Backtrader Technical Analysis Advisor, an AI agent specializing in
comprehensive technical analysis of a Backtrader strategy's data. You function as
a component in a multi-agent advisory system, where your sole responsibility is to
evaluate price action and technical indicators in order to produce a structured
technical outlook.

---

INPUT
All input is provided as markdown tables in chronological ascending order (oldest at top, latest at bottom). The input consists of:
DataFeed Table
    - Includes OHLCV or other price/volume-related information from the strategy
Indicator Table
    - Includes all technical indicators currently used by the strategy

---

TASK
1.	Evaluate every row and column in both DataFeeds and Indicators tables. No data may be ignored.
2.	Perform a full technical analysis using the most recent state of the data, identifying:
    - Trends (e.g., bullish/bearish continuation or reversal)
    - Momentum shifts
    - Overbought/oversold conditions
    - Volatility signals
    - Support/resistance zones (if applicable from data)
3.	Summarize your findings in a structured format.
4.	Assign a confidence score between 0.0 and 1.0, based on how clearly the data supports your analysis.

---

IMPORTANT CONSTRAINS
    - Do not emit more than one signal.
    - Do not invent data or signals — your response must be directly supported by the latest available data.
    - Your signal is used to guide the next trade decision immediately after the current data.

---"""


class BacktraderTechnicalAnalysisAdvisor(BacktraderLLMAdvisor):
    """Technical analiysis advisor

    This advisor analyzes the strategy data and indicators.
    """

    advisor_instructions = ADVISOR_INSTRUCTIONS

    def update_state(
        self, state: LLMAdvisorUpdateStateData
    ) -> LLMAdvisorUpdateStateData:
        """Default update_state method which uses all available strategy data

        To modify the data that the advisor is using, this method needs to be
        overwritten."""
        self.advisor_messages_input.advisor_prompt = state.messages[0].content
        self.advisor_messages_input.advisor_data = compile_data_artefacts(
            self._get_technical_analysis_data(state) + state.data
        )
        return self._update_state(state)

    def _get_technical_analysis_data(
        self, state: LLMAdvisorState
    ) -> list[LLMAdvisorDataArtefact]:
        """Returns default strategy data"""
        strategy = get_strategy_from_state(state)
        data_feeds_data = {
            get_data_feed_name(data_feed): generate_data_feed_data(
                data_feed=data_feed,
                lookback_period=state.metadata["data_lookback_period"],
            )
            for data_feed in strategy.datas
        }
        indicators_data = {
            get_indicator_name(indicator): generate_indicator_data(
                indicator=indicator,
                lookback_period=state.metadata["indicator_lookback_period"],
            )
            for indicator in strategy.getindicators()
            if show_lineroot_obj(indicator)
        }
        response = []
        for data_feed_data in data_feeds_data.values():
            response.append(
                LLMAdvisorDataArtefact(
                    description=f"DataFeed {data_feed_data.name}",
                    artefact=data_feed_data.data,
                    output_mode=LLMAdvisorDataArtefactOutputMode.MARKDOWN_TABLE,
                )
            )
        for indicator_data in indicators_data.values():
            response.append(
                LLMAdvisorDataArtefact(
                    description=f"Indicator {indicator_data.name}",
                    artefact=indicator_data.data,
                    output_mode=LLMAdvisorDataArtefactOutputMode.MARKDOWN_TABLE,
                )
            )
        return response
