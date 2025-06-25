from typing import Any

import backtrader as bt

from llm_advisory.pydantic_models import LLMAdvisorState

from bt_llm_advisory.pydantic_models import (
    BacktraderStrategyData,
    BacktraderBrokerData,
    BacktraderPositionData,
    BacktraderPositionsData,
    BacktraderDataFeedData,
    BacktraderIndicatorData,
    BacktraderAnalyzerData,
)


def get_clock_from_lineroot(
    lineroot_obj: bt.LineRoot, resolve_to_data: bool = False
) -> bt.LineRoot:
    """
    Returns a clock object to use for building data
    A clock object can be either a strategy, data source,
    indicator or a observer.
    """
    if isinstance(lineroot_obj, bt.LinesOperation):
        # indicators can be created to run on a line
        # (instead of e.g. a data object) in that case grab
        # the owner of that line to find the corresponding clock
        # also check for line actions like "macd > data[0]"
        return get_clock_from_lineroot(lineroot_obj._clock, resolve_to_data)
    elif isinstance(lineroot_obj, (bt.LineSingle)):
        # if we have a line, return its owners clock
        return get_clock_from_lineroot(lineroot_obj._owner, resolve_to_data)
    elif isinstance(lineroot_obj, bt.LineSeriesStub):
        # if its a LineSeriesStub object, take the first line
        # and get the clock from it
        return get_clock_from_lineroot(lineroot_obj.lines[0], resolve_to_data)
    elif isinstance(lineroot_obj, (bt.IndicatorBase, bt.MultiCoupler, bt.ObserverBase)):
        # a indicator and observer can be a clock, internally
        # it is obj._clock
        if resolve_to_data:
            return get_clock_from_lineroot(lineroot_obj._clock, resolve_to_data)
        clock = lineroot_obj
    elif isinstance(lineroot_obj, bt.StrategyBase):
        # a strategy can be a clock, internally it is obj.data
        clock = lineroot_obj
    elif isinstance(lineroot_obj, bt.AbstractDataBase):
        clock = lineroot_obj
    else:
        raise Exception(
            f"Unsupported line root object: {lineroot_obj.__class__.__name__}"
        )
    return clock


def show_lineroot_obj(lineroot_obj: bt.LineRoot) -> bool:
    try:
        if not lineroot_obj.plotinfo.plot or lineroot_obj.plotinfo.plotskip:
            return False
        return True
    except AttributeError:
        return False  # no plotinfo


def get_strategy_from_state(state: LLMAdvisorState) -> bt.Strategy:
    """Returns the strategy from a state"""
    strategy = state.metadata.get("strategy")
    if strategy is None:
        raise ValueError("strategy not found in state metadata")
    return strategy


def get_instruments(strategy: bt.Strategy) -> list[str]:
    """Returns all instruments used by the strategy"""
    return list({get_data_feed_instrument(data_feed) for data_feed in strategy.datas})


def get_data_feed_name(data_feed: bt.DataBase) -> str:
    """Returns the data feed name"""
    return f"{get_data_feed_instrument(data_feed)}[{get_resolution_name(data_feed)}]"


def get_data_feed_instrument(data_feed: bt.DataBase) -> str:
    if isinstance(data_feed, bt.DataClone):
        return str(data_feed.data._name)
    return str(data_feed._name)


def get_indicator_name(indicator: bt.IndicatorBase) -> str:
    """Returns a indicator name"""
    name = indicator.__class__.__name__
    if hasattr(indicator, "plotinfo") and indicator.plotinfo.plotname:
        name = indicator.plotinfo.plotname
    return f"{name}{indicator._plotlabel() if hasattr(indicator, "_plotlabel") else ""}"


def get_analyzer_name(analyzer: bt.Analyzer) -> str:
    """Returns the analyzer name"""
    return f"{analyzer.__class__.__name__}"


def get_resolution_name(data_feed: bt.DataBase) -> str:
    """Returns a human readable resolution name for the given timeframe/compression"""
    timeframe, compression = data_feed._timeframe, data_feed._compression
    return (
        f"{'' if timeframe is bt.TimeFrame.Ticks else str(compression) + ' '}"
        f"{bt.TimeFrame.getname(timeframe, compression)}"
    )


def generate_strategy_data(
    strategy: bt.Strategy, add_indicators: bool = True, add_analyzers: bool = False
) -> BacktraderStrategyData:
    """Generates strategy data"""
    strategy_name = strategy.__class__.__name__
    data_names = []
    instrument_names = []
    indicator_names = []
    analyzer_names = []
    for data in strategy.datas:
        data_names.append(get_data_feed_name(data))
        instrument_names.append(get_data_feed_instrument(data))
    if add_indicators:
        for indicator in strategy.getindicators():
            if not show_lineroot_obj(indicator):
                continue
            indicator_name = get_indicator_name(indicator)
            indicator_names.append(indicator_name)
    if add_analyzers:
        for analyzer in strategy.analyzers:
            analyzer_name = get_analyzer_name(analyzer)
            analyzer_names.append(analyzer_name)
    description = (
        f"This is an overview of the trading strategy {strategy_name}."
        f"\nDataFeeds in use: {",".join(list(data_names))}."
    )
    if len(indicator_names) > 0:
        description += f"\nIndicators in use: {",".join(list(indicator_names))}"
    if len(analyzer_names) > 0:
        description += f"\nAnalyzers in use: {",".join(list(analyzer_names))}"
    return BacktraderStrategyData(
        name=strategy_name,
        description=description,
        data_names=data_names,
        instrument_names=instrument_names,
        indicator_names=indicator_names,
        analyzer_names=analyzer_names,
    )


def generate_broker_data(strategy: bt.Strategy) -> BacktraderBrokerData:
    """Generates broker data"""
    broker = strategy.broker
    cash = broker.get_cash()
    value = broker.get_value()
    margin = cash - value
    description = f"A total value of {value:.2f}USD is available for trading."
    if margin > 0:
        description += f" Currently a margin of {margin:.2f}USD is used."

    return BacktraderBrokerData(
        description=description, cash=cash, value=value, margin=margin
    )


def generate_positions_data(strategy: bt.Strategy) -> BacktraderPositionsData:
    """Generates positions data"""
    positions = {}
    broker = strategy.broker
    for data_feed in strategy.datas:
        position = broker.getposition(data_feed)
        data_instrument = get_data_feed_instrument(data_feed)
        size = position.size
        price = position.price
        if data_instrument in positions:
            if not size and not price:
                continue
            positions[data_instrument].position_size += size
            positions[data_instrument].position_price = (positions[data_instrument].position_price + price) / 2
        else:
            positions[data_instrument] = BacktraderPositionData(
                position_size=size, position_price=price
            )
    return BacktraderPositionsData(positions=positions)


def generate_data_feed_data(
    data_feed: bt.DataBase,
    lookback_period: int,
    only_close: bool = False,
    add_volume: bool = True,
) -> BacktraderDataFeedData:
    """Generates data feed data"""
    name = get_data_feed_name(data_feed)
    instrument = get_data_feed_instrument(data_feed)
    resolution = get_resolution_name(data_feed)
    data: list[dict[str, Any]] = []
    for i in range(lookback_period):
        try:
            feed_data_row = {
                "datetime": data_feed.datetime.datetime(-i),
            }
            if only_close:
                feed_data_row["close"] = data_feed.close[-i]
            else:
                feed_data_row["open"] = data_feed.open[-i]
                feed_data_row["high"] = data_feed.high[-i]
                feed_data_row["low"] = data_feed.low[-i]
                feed_data_row["close"] = data_feed.close[-i]
            if add_volume:
                feed_data_row["volume"] = data_feed.volume[-i]
            data.append(feed_data_row)
        except Exception:
            break
    return BacktraderDataFeedData(
        name=name,
        instrument=instrument,
        resolution=resolution,
        data=data,
    )


def generate_indicator_data(
    indicator: bt.IndicatorBase | bt.LinesOperation, lookback_period: int
) -> BacktraderIndicatorData:
    """Generates indicator data"""
    indicator_name = (
        get_indicator_name(indicator)
        if isinstance(indicator, bt.IndicatorBase)
        else indicator.__class__.__name__
    )
    data_for_indicator = get_clock_from_lineroot(indicator, True)
    indicator_data = []
    for i in range(lookback_period):
        lines = {"datetime": data_for_indicator.datetime.datetime(-i)}
        if isinstance(indicator, bt.IndicatorBase):
            line_aliases = indicator.getlinealiases()
            for line_alias in line_aliases:
                line = getattr(indicator, line_alias)
                line_name = f"{get_indicator_name(indicator)}.{line_alias}"
                try:
                    line_value = line[-i]
                except Exception:
                    line_value = float("nan")
                lines[line_name] = line_value
        elif isinstance(indicator, bt.LinesOperation):
            lines[get_indicator_name(indicator)] = indicator[-i]
        else:
            raise ValueError(f"Unkown indicator type: {indicator.__class__.__name__}")
        indicator_data.append(lines)
    return BacktraderIndicatorData(name=indicator_name, data=indicator_data)


def generate_analyzer_data(analyzer: bt.Analyzer) -> BacktraderAnalyzerData:
    """Generates analyzer data"""
    analyzer_name = get_analyzer_name(analyzer)
    analyzer_data = [analyzer.get_analysis()]
    return BacktraderAnalyzerData(name=analyzer_name, data=analyzer_data)
