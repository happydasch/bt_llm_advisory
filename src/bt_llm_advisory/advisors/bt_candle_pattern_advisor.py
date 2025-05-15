import backtrader as bt

from llm_advisory.helper.llm_prompt import compile_data_artefacts
from llm_advisory.pydantic_models import (
    LLMAdvisorDataArtefact,
    LLMAdvisorDataArtefactOutputMode,
    LLMAdvisorUpdateStateData,
)

from bt_llm_advisory import BacktraderLLMAdvisor
from bt_llm_advisory.helper.bt_data_generation import (
    generate_data_feed_data,
    get_strategy_from_state,
)


ADVISOR_INSTRUCTIONS = """
You are the Backtrader Candle Pattern Advisor, an AI agent specializing in detecting
classic candlestick chart patterns using OHLC data. You operate within a multi-agent
advisory system where your sole responsibility is to analyze recent market behavior and
emit one valid candlestick pattern signal.

⸻

DATA FORMAT
You are provided with OHLC (Open, High, Low, Close) candle data in ascending chronological order:
    - datetime (UTC)
    - open (float)
    - high (float)
    - low (float)
    - close (float)

The latest data is at the bottom. Use all candles in your analysis.

---

TASK
1.  Analyze the entire OHLC dataset.
2.  Detect one valid candlestick pattern based on the most recent candle(s) (typically last 1–3 candles).
3.  Your response must begin with the exact name of the pattern you detect.
4.  Provide a short, precise reasoning justifying the match.
5.  Output a confidence score from 0.0 (no confidence) to 1.0 (high confidence), reflecting how well
    the recent candle(s) match the expected criteria.

⸻

IMPORTANT CONSTRAINS
- Do not emit more than one signal.
- Do not invent data or signals — your response must be directly supported by the latest available data.
- Your signal is used to guide the next trade decision immediately after the current data.

---"""


class BacktraderCandlePatternAdvisor(BacktraderLLMAdvisor):
    """Candle pattern advisor

    This advisor identifies candlestick patterns on OHLC data.
    """

    advisor_instructions = ADVISOR_INSTRUCTIONS

    def __init__(
        self,
        lookback_period: int = 5,  # lookback period for ohlc data
        add_all_data_feeds: bool = False,  # should all data feeds be included
    ):
        super().__init__()
        self.lookback_period = lookback_period
        self.add_all_data_feeds = add_all_data_feeds

    def update_state(
        self, state: LLMAdvisorUpdateStateData
    ) -> LLMAdvisorUpdateStateData:
        self.advisor_messages_input.advisor_prompt = state.messages[0].content
        strategy = get_strategy_from_state(state)
        data_feeds = (
            [strategy.datas[0]] if not self.add_all_data_feeds else strategy.datas
        )
        data_feed_data = self._get_ohlc_data(data_feeds, self.lookback_period)
        self.advisor_messages_input.advisor_data = compile_data_artefacts(
            data_feed_data
        )
        return self._update_state(state)

    def _get_ohlc_data(
        self, data_feeds: list[bt.DataBase], lookback_period: int
    ) -> list[LLMAdvisorDataArtefact]:
        ohlc_data = []
        for data_feed in data_feeds:
            feed_data = generate_data_feed_data(
                data_feed=data_feed,
                lookback_period=lookback_period,
                only_close=False,
                add_volume=False,
            )
            ohlc_data.append(
                LLMAdvisorDataArtefact(
                    description=f"DataFeed {feed_data.name}",
                    artefact=feed_data.data,
                    output_mode=LLMAdvisorDataArtefactOutputMode.MARKDOWN_TABLE,
                )
            )
        return ohlc_data
