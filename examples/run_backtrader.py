import os
import backtrader as bt


from bt_llm_advisory import BacktraderLLMAdvisory
from bt_llm_advisory.advisors import (
    BacktraderStrategyAdvisor,
    BacktraderPersonaAdvisor,
    BacktraderFeedbackAdvisor,
    BacktraderCandlePatternAdvisor,
    BacktraderTechnicalAnalysisAdvisor,
    BacktraderTrendAdvisor,
    BacktraderReversalAdvisor,
)

from llm_strategy import LLMStrategy

bot_advisory = BacktraderLLMAdvisory(
    max_concurrency=1,
    model_provider_name="ollama",  # openai, ollama
    # openai models: gpt-4.5-preview, gpt-4o, o3, o4-mini
    # ollama models: gemma3, gemma3:12b, gemma3:27b, qwen2.5, qwen2.5:32b, llama3.1:latest, llama3.3:70b-instruct-q4_0, mistral-small3.1, deepseek-r1
    model_config={
        "OPENAI_MODEL_NAME": "gpt-4o",
        "OPENAI_API_KEY": "",
        "OLLAMA_MODEL_NAME": "qwen2.5",
    },
    advisors=[
        BacktraderStrategyAdvisor(),
        BacktraderReversalAdvisor(
            long_ma_period=25,
            short_ma_period=10,
            lookback_period=10,
            add_all_data_feeds=True,
        ),
        BacktraderTrendAdvisor(
            long_ma_period=25,
            short_ma_period=10,
            lookback_period=10,
            add_all_data_feeds=True,
        ),
        # BacktraderStrategyAdvisor(),
        # BacktraderTechnicalAnalysisAdvisor(),
        # BacktraderCandlePatternAdvisor(lookback_period=10, add_all_data_feeds=True),
        # BacktraderFeedbackAdvisor(),
        # BacktraderPersonaAdvisor("Technical advisor", "intraday trader"),
        # BacktraderPersonaAdvisor(
        #     "Warren Buffett",
        #     (
        #         "A long-term fundamental investor who avoids market noise and focuses on intrinsic value.\n"
        #         "Preferred Investment Types: stocks, private equity\n"
        #         "Preferred Timeframes: monthly to yearly\n"
        #         "Special Knowledge: business valuation, economic moats, compound interest\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Paul Tudor Jones",
        #     (
        #         "A tactical trader with an edge in reading market psychology and momentum.\n"
        #         "Preferred Investment Types: forex, commodities, equities\n"
        #         "Preferred Timeframes: 4H to daily\n"
        #         "Special Knowledge: macro fundamentals, technical divergence, volatility spikes\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Stanley Druckenmiller",
        #     (
        #         "An adaptive macro investor with a strong sense for capital flow shifts.\n"
        #         "Preferred Investment Types: forex, equities, crypto\n"
        #         "Preferred Timeframes: swing (daily-weekly)\n"
        #         "Special Knowledge: macro narrative interpretation, position sizing, liquidity cycles\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Jesse Livermore",
        #     (
        #         "A classic trend follower and breakout trader.\n"
        #         "Preferred Investment Types: stocks, commodities\n"
        #         "Preferred Timeframes: daily to weekly\n"
        #         "Special Knowledge: price action, market timing, pyramiding\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Linda Raschke",
        #     (
        #         "A short-term technical trader who thrives in fast-moving markets.\n"
        #         "Preferred Investment Types: futures, forex\n"
        #         "Preferred Timeframes: 15-min to 4H\n"
        #         "Special Knowledge: market structure, oscillator timing, mean-reversion setups\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Peter Brandt",
        #     (
        #         "A disciplined classical chartist focusing on well-defined pattern setups.\n"
        #         "Preferred Investment Types: commodities, crypto, forex\n"
        #         "Preferred Timeframes: daily to weekly\n"
        #         "Special Knowledge: chart patterns, breakout confirmation, risk management\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Michael Burry",
        #     (
        #         "A contrarian value investor with a specialty in crisis detection.\n"
        #         "Preferred Investment Types: equities, CDS, macro derivatives\n"
        #         "Preferred Timeframes: multi-week to multi-year\n"
        #         "Special Knowledge: forensic analysis, systemic risk detection\n"
        #     ),
        # ),
        # BacktraderPersonaAdvisor(
        #     "Richard Dennis",
        #     (
        #         "A trend-following system trader using strict entry/exit rules.\n"
        #         "Preferred Investment Types: futures, commodities, forex\n"
        #         "Preferred Timeframes: daily\n"
        #         "Special Knowledge: Turtle Trading rules, volatility-based risk control, position scaling\n"
        #     ),
        # ),
    ],
)


cerebro = bt.Cerebro()

current_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_dir, "orcl-1995-2014.txt")

data0 = bt.feeds.YahooFinanceCSVData(dataname=data_file)

cerebro.addstrategy(LLMStrategy, bot_advisory)
cerebro.adddata(data0)

cerebro.run()
cerebro.plot()
