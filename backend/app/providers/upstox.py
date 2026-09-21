"""Upstox market-data provider adapter.

Provider transport and normalization are kept separate from FastAPI routes. This
module never places orders, logs credentials, or fabricates market observations.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, TypeAlias
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.core.config import settings
from app.providers.base import MarketDataProvider, ProviderNotConfigured

ProviderRecord: TypeAlias = dict[str, Any]


class ProviderRequestError(RuntimeError):
    """Base error for controlled market-provider failures."""


class ProviderAuthenticationError(ProviderRequestError):
    """The provider rejected the configured access token."""


class ProviderRateLimitError(ProviderRequestError):
    """The provider rejected a request because of rate limiting."""


class ProviderResponseError(ProviderRequestError):
    """The provider returned an unexpected or malformed response."""


@dataclass(frozen=True)
class _UpstoxHttpClient:
    """Minimal asynchronous HTTP facade using the standard library."""

    access_token: str
    timeout: float = 10.0
    base_url: str = "https://api.upstox.com"

    async def get(
        self, path: str, params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        query = ""
        if params:
            query = "?" + "&".join(
                f"{quote(key)}={quote(value)}" for key, value in params.items()
            )
        request = Request(
            f"{self.base_url}{path}{query}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
            method="GET",
        )
        try:
            raw = await asyncio.to_thread(self._read, request)
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderAuthenticationError("Upstox authentication failed.") from None
            if exc.code == 429:
                raise ProviderRateLimitError("Upstox rate limit reached.") from None
            raise ProviderRequestError(
                f"Upstox request failed with HTTP {exc.code}."
            ) from None
        except (TimeoutError, URLError, OSError):
            raise ProviderRequestError(
                "Unable to reach the Upstox market-data service."
            ) from None

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise ProviderResponseError("Upstox returned invalid JSON.") from None
        if not isinstance(payload, dict):
            raise ProviderResponseError("Upstox returned an unexpected response.")
        return payload

    def _read(self, request: Request) -> bytes:
        with urlopen(request, timeout=self.timeout) as response:
            return response.read()


class UpstoxProvider(MarketDataProvider):
    """Async adapter for Upstox market-data endpoints.

    Symbols are Upstox instrument keys, typically sourced from the official
    instrument master outside this provider. No symbol mapping is guessed here.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("Provider timeout must be positive.")
        self._timeout = timeout

    def _client(self) -> _UpstoxHttpClient:
        token = settings.upstox_access_token
        if not token:
            raise ProviderNotConfigured("API_NOT_CONFIGURED")
        return _UpstoxHttpClient(access_token=token, timeout=self._timeout)

    @staticmethod
    def _data(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ProviderResponseError("Upstox response did not contain an object payload.")
        return data

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        value = symbol.strip()
        if not value or len(value) > 200:
            raise ProviderRequestError("A valid Upstox instrument key is required.")
        return value

    async def search(self, query: str) -> list[ProviderRecord]:
        """Search configured instruments without fabricating search results."""
        self._client()
        if not query.strip():
            return []
        raise ProviderRequestError(
            "Upstox instrument-master search is not configured."
        )

    async def search_stocks(self, query: str) -> list[ProviderRecord]:
        """Search instruments using the configured instrument-master integration."""
        return await self.search(query)

    async def quote(self, symbol: str) -> ProviderRecord:
        """Fetch a quote for an Upstox instrument key."""
        client = self._client()
        payload = await client.get(
            "/v2/market-quote/quotes",
            {"instrument_key": self._validate_symbol(symbol)},
        )
        return self._data(payload)

    async def get_quote(self, symbol: str) -> ProviderRecord:
        """Fetch a quote using the provider-specific method name."""
        return await self.quote(symbol)

    async def history(self, symbol: str, interval: str) -> list[ProviderRecord]:
        """Fetch historical candles for an Upstox instrument key.

        ``interval`` is expected in Upstox form, for example ``1d`` or ``30m``.
        The returned records remain provider-shaped for a separate normalizer.
        """
        value = interval.strip().lower()
        if len(value) < 2 or not value[:-1].isdigit() or value[-1] not in {"m", "h", "d", "w"}:
            raise ProviderRequestError("Unsupported Upstox candle interval.")
        client = self._client()
        payload = await client.get(
            f"/v2/historical-candle/{quote(self._validate_symbol(symbol), safe='')}/{quote(value)}"
        )
        candles = self._data(payload).get("candles")
        if not isinstance(candles, list):
            raise ProviderResponseError("Upstox response did not contain candles.")
        return [candle for candle in candles if isinstance(candle, dict)]

    async def get_history(self, symbol: str, interval: str) -> list[ProviderRecord]:
        """Fetch historical candles using the provider-specific method name."""
        return await self.history(symbol, interval)

    async def get_market_indices(
        self, instrument_keys: list[str]
    ) -> list[ProviderRecord]:
        """Fetch quotes for explicitly configured index instrument keys."""
        if not instrument_keys:
            return []
        client = self._client()
        keys = [self._validate_symbol(key) for key in instrument_keys]
        data = self._data(
            await client.get("/v2/market-quote/quotes", {"instrument_key": ",".join(keys)})
        )
        return [value for value in data.values() if isinstance(value, dict)]
