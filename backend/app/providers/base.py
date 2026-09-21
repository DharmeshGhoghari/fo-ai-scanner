from abc import ABC, abstractmethod
from typing import Any

class ProviderNotConfigured(RuntimeError): pass
class MarketDataProvider(ABC):
    @abstractmethod
    async def quote(self, symbol: str) -> dict[str, Any]: ...
    @abstractmethod
    async def history(self, symbol: str, interval: str) -> list[dict[str, Any]]: ...
    async def search(self, query: str) -> list[dict[str, Any]]: return []
class NewsProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[dict[str, Any]]: ...
class FundamentalsProvider(ABC):
    @abstractmethod
    async def get(self, symbol: str) -> dict[str, Any]: ...
class AIProvider(ABC):
    @abstractmethod
    async def explain(self, payload: dict[str, Any]) -> dict[str, Any]: ...
