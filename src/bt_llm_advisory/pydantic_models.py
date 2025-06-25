from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field
from llm_advisory.pydantic_models import LLMAdvisorSignal, LLMAdvisorAdvice


class BacktraderLLMAdvisorSignal(LLMAdvisorSignal):
    """Signal used by backtrader advisory"""

    signal: Literal["bullish", "bearish", "neutral", "none"] = Field(
        default="none",
        description="Trading advice based on advisors signals",
    )


class BacktraderLLMAdvisorAdvice(LLMAdvisorAdvice):
    """Signal for state advice"""

    signal: Literal["buy", "sell", "close", "none"] = Field(
        default="none",
        description="Advice strategy based on advisors signals",
    )


class BacktraderStrategyData(BaseModel):
    """Model for strategy data"""

    name: str
    description: str
    data_names: list[str]
    instrument_names: list[str]
    indicator_names: list[str]
    analyzer_names: list[str]


class BacktraderBrokerData(BaseModel):
    """Model for broker data"""

    description: str
    cash: float
    value: float
    margin: float


class BacktraderPositionData(BaseModel):
    """Model for position data"""

    position_size: float
    position_price: float


class BacktraderPositionsData(BaseModel):
    """Model for positions data"""

    positions: dict[str, BacktraderPositionData]


class BacktraderDataFeedData(BaseModel):
    """Model for data feed data"""

    name: str
    instrument: str
    resolution: str
    data: list[dict[str, datetime | float]]


class BacktraderIndicatorData(BaseModel):
    """Model for indicator data"""

    name: str
    data: list[dict[str, datetime | float]]


class BacktraderAnalyzerData(BaseModel):
    """Model for analyzer data"""

    name: str
    data: list[dict[str, datetime | float]]
