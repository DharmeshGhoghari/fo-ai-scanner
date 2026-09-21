from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class ApiStatus(BaseModel):
    status: str = "API_NOT_CONFIGURED"
    symbol: str | None = None
    message: str = "Market data provider is not configured."


class SearchResponse(BaseModel):
    status: str = "API_NOT_CONFIGURED"
    query: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    message: str = "Market data provider is not configured."


class StockResponse(ApiStatus):
    company_name: str | None = None
    exchange: str | None = None
    sector: str | None = None
    data_source: str | None = None


class QuoteResponse(ApiStatus):
    last_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    timestamp: str | None = None


class HistoryResponse(ApiStatus):
    timeframe: str
    candles: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: str | None = None


class TechnicalsResponse(ApiStatus):
    indicators: dict[str, Any] = Field(default_factory=lambda: {
        "sma": None, "ema": None, "rsi": None, "macd": None,
        "bollinger_bands": None, "vwap": None, "atr": None,
        "stochastic": None, "support_resistance": None,
    })


class FundamentalsResponse(ApiStatus):
    fundamentals: dict[str, Any] = Field(default_factory=lambda: {
        "market_cap": None, "revenue": None, "revenue_growth": None,
        "net_profit": None, "profit_growth": None, "eps": None,
        "pe": None, "pb": None, "roe": None, "roce": None,
        "debt": None, "debt_to_equity": None, "margins": None,
        "dividend": None, "dividend_yield": None, "cash_flow": None,
    })


class NewsResponse(ApiStatus):
    items: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisResponse(ApiStatus):
    ai_generated: bool = False
    analysis: dict[str, Any] = Field(default_factory=dict)


def _status(symbol: str | None = None) -> dict[str, Any]:
    return {
        "status": "API_NOT_CONFIGURED",
        "symbol": symbol,
        "message": "Market data provider is not configured.",
    }


def _symbol(value: str) -> str:
    normalized = value.strip().upper()
    if not normalized or len(normalized) > 30:
        raise HTTPException(status_code=422, detail="A valid stock symbol is required.")
    return normalized


@router.get("/search", response_model=SearchResponse)
async def search_stocks(q: str = Query(..., min_length=1, max_length=50)) -> SearchResponse:
    return SearchResponse(query=q.strip(), results=[])


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(symbol: str) -> StockResponse:
    return StockResponse(**_status(_symbol(symbol)))


@router.get("/{symbol}/quote", response_model=QuoteResponse)
async def get_quote(symbol: str) -> QuoteResponse:
    return QuoteResponse(**_status(_symbol(symbol)))


@router.get("/{symbol}/history", response_model=HistoryResponse)
async def get_history(symbol: str, timeframe: str = Query("1Y", min_length=1, max_length=10)) -> HistoryResponse:
    return HistoryResponse(**_status(_symbol(symbol)), timeframe=timeframe, timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/{symbol}/technicals", response_model=TechnicalsResponse)
async def get_technicals(symbol: str) -> TechnicalsResponse:
    return TechnicalsResponse(**_status(_symbol(symbol)))


@router.get("/{symbol}/fundamentals", response_model=FundamentalsResponse)
async def get_fundamentals(symbol: str) -> FundamentalsResponse:
    return FundamentalsResponse(**_status(_symbol(symbol)))


@router.get("/{symbol}/news", response_model=NewsResponse)
async def get_news(symbol: str) -> NewsResponse:
    return NewsResponse(**_status(_symbol(symbol)), items=[])


@router.get("/{symbol}/analysis", response_model=AnalysisResponse)
async def get_analysis(symbol: str) -> AnalysisResponse:
    return AnalysisResponse(**_status(_symbol(symbol)), ai_generated=False, analysis={})
