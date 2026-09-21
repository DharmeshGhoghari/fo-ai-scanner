from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StockSearchResult(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    status: str = "API_NOT_CONFIGURED"


class StockSearchResponse(BaseModel):
    status: str = "API_NOT_CONFIGURED"
    query: str
    results: list[StockSearchResult] = Field(default_factory=list)


class StockQuote(BaseModel):
    symbol: str
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[datetime] = None
    status: str = "API_NOT_CONFIGURED"


class OHLCVBar(BaseModel):
    timestamp: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None


class StockHistoryResponse(BaseModel):
    symbol: str
    timeframe: str
    bars: list[OHLCVBar] = Field(default_factory=list)
    status: str = "API_NOT_CONFIGURED"


class BollingerBands(BaseModel):
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None


class MACD(BaseModel):
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None


class Stochastic(BaseModel):
    k: Optional[float] = None
    d: Optional[float] = None


class TechnicalIndicators(BaseModel):
    sma: Optional[float] = None
    ema: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[MACD] = None
    bollinger_bands: Optional[BollingerBands] = None
    vwap: Optional[float] = None
    atr: Optional[float] = None
    stochastic: Optional[Stochastic] = None
    support: Optional[float] = None
    resistance: Optional[float] = None
    status: str = "API_NOT_CONFIGURED"


class StockFundamentals(BaseModel):
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    net_profit: Optional[float] = None
    profit_growth: Optional[float] = None
    eps: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    debt: Optional[float] = None
    debt_to_equity: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    dividend: Optional[float] = None
    dividend_yield: Optional[float] = None
    cash_flow: Optional[float] = None
    status: str = "API_NOT_CONFIGURED"


class NewsItem(BaseModel):
    headline: str
    source: Optional[str] = None
    timestamp: Optional[datetime] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    ai_summary: Optional[str] = None


class StockNewsResponse(BaseModel):
    symbol: str
    items: list[NewsItem] = Field(default_factory=list)
    status: str = "API_NOT_CONFIGURED"


class StockAnalysisResponse(BaseModel):
    symbol: str
    summary: Optional[str] = None
    positives: list[str] = Field(default_factory=list)
    negatives: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    technical_summary: Optional[str] = None
    fundamental_summary: Optional[str] = None
    news_summary: Optional[str] = None
    missing_data: list[str] = Field(default_factory=list)
    generated_at: Optional[datetime] = None
    status: str = "API_NOT_CONFIGURED"
