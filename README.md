# Backtrader LLM Advisory

`Backtrader LLM Advisory` is using `LLM Advisory` for providing advisors to backtrader strategies. It allows the strategy to access different "advisors" which have access to the strategy and its current state.

inside the strategy init call `llm_advisory.init(self)` from next call `llm_advisory.get_advice()`

- Generates automatically data from a strategy and uses this for advisory data
- Control lookback period of data to use

## Usecase scenarios

- Confirm trend, identify sideways trends using the trend advisor
- Interpret current indicator values by the technical analysis advisor
- Get trading signals by asking the technical analysis advisor to check current indicator values
- Identify candle patterns by using the candle pattern advisor
- Confirm a signal from your strategy code by advisory
- Get feedback about your strategy and the current trading session

## Available Advisors

An overview of all available advisors with a short explaination.

### BacktraderStrategyAdvisor

Common advisor for strategies. Takes available information from strategy and provides an advice based on this data.

```python
from bt_llm_advisory.advisors import BacktraderStrategyAdvisor

strategy_advisor = BacktraderStrategyAdvisor()
```

### BacktraderTrendAdvisor

Returns a signal based on data from the current strategy. The signal is bullish for a up-trend, bearish for a down-trend, neutral for no-trend and none if unable to identify.
This advisor uses different indicators to identify the current trend.

```python
from bt_llm_advisory.advisors import BacktraderTrendAdvisor

trend_advisor = BacktraderTrendAdvisor(
    short_ma_period: int = 10,  # period for short moving average
    long_ma_period: int = 25,  # period for long moving average
    lookback_period: int = 5,  # lookback period for trend data
    add_all_data_feeds: bool = False,  # should all data feeds be included
)
```

### BacktraderTechnicalAnalysisAdvisor

Returns a signal based on a technical analysis of the strategy indicators.

```python
from bt_llm_advisory.advisors import BacktraderTechnicalAnalysisAdvisor

technial_analysis_advisor = BacktraderTechnicalAnalysisAdvisor()
```

### BacktraderCandlePatternAdvisor

Returns a signal from OHLC candles if it recognizes a candlestick pattern.

```python
from bt_llm_advisory.advisors import BacktraderCandlePatternAdvisor

candle_pattern_advisor = BacktraderCandlePatternAdvisor(
    lookback_period: int = 5,  # lookback period for ohlc data
    add_all_data_feeds: bool = False,  # should all data feeds be included
)
```

### BacktraderFeedbackAdvisor

Provides feedback about the strategies data.

```python
from bt_llm_advisory.advisors import BacktraderFeedbackAdvisor

feedback_advisor = BacktraderFeedbackAdvisor()
```

### BacktraderPersonaAdvisor

Strategy trading advisor with additional defined personaily or more detailed instructions.

```python
from bt_llm_advisory.advisors import BacktraderPersonaAdvisor

persona_advisor = BacktraderPersonaAdvisor(
    # name of the persona, can also be a famous person
    person_name: str,
    # description of the personality, which also can contain informations about needed knowledge
    personality: str
)
```

## Examples

## Frequently Asked Questions

TODO

- add possibility to instruct another llm to create / update the used strategy based on advisors input
- Update code of strategy by asking a llm for a change
- Trade based on advisors advices
