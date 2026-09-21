"""Upstox market-data provider adapter.

This module contains provider transport and response normalization only. It does
not place orders and never returns fabricated market observations.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote as url_quote
from urllib.request import Request, urlopen

from app.core.config import settings
from app.providers.base import MarketDataProvider, ProviderNotConfigured


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
    """Small async facade over the standard-library HTTP client."""

    access_token: str
    timeout: float = 10.0
    base_url: str = "https://api.upstox.com"

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        query = ""
        if params:
            query = "?" + "&".join(
                f"{url_quote(key)}={url_quote(value)}" for key, value in params.items()
            )
        url = f"{self.base_url}{path}{query}"
        request = Request(
            url,
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
            raise ProviderRequestError(f"Upstox request failed with HTTP {exc.code}.") from None
        except (TimeoutError, URLError, OSError):
            raise ProviderRequestError("Unable to reach the Upstox market-data service.") from None

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

    ``symbol`` arguments are Upstox instrument keys, such as the keys from the
    official instrument master. Symbol discovery is intentionally not guessed;
    callers should supply or maintain that mapping outside this adapter.
    """

    def __init__(self, timeout: float = 10.0) -> None:
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

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Return provider search results when a supported search endpoint exists.

        Upstox instrument discovery is normally performed from its instrument
        master file. This adapter does not fabricate search results or download
        and cache that mapping implicitly, so it reports the unconfigured state.
        """
        self._client()
        if not query.strip():
            return []
        raise ProviderRequestError("Upstox instrument-master search is not configured.")

    async def search_stocks(self, query: str) -> list[dict[str, Any]]:
        """Search instruments using the provider's configured instrument mapping."""
        return await self.search(query)

    async def quote(self, symbol: str) -> dict[str, Any]:
        """Fetch a quote for an Upstox instrument key."""
        client = self._client()
        payload = await client.get(
            "/v2/market-quote/quotes",
            {"instrument_key": symbol},
        )
        return self._data(payload)

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """Fetch a quote using an explicit provider-style method name."""
        return await self.quote(symbol)

    async def history(self, symbol: str, interval: str) -> list[dict[str, Any]]:
        """Fetch historical candles for an Upstox instrument key and interval."""
        client = self._client()
        parts = interval.split("_")
        if len(parts) != 2 or parts[0] not in {"1", "5", "10", "15", "30", "60"}:
            raise ProviderRequestError("Unsupported Upstox candle interval.")
        unit, value = parts
        payload = await client.get(
            f"/v2/historical-candle/{url_quote(symbol, safe='')}/{unit}/{value}",
        )
        data = self._data(payload)
        candles = data.get("candles")
        if not isinstance(candles, list):
            raise ProviderResponseError("Upstox response did not contain candles.")
        return [candle for candle in candles if isinstance(candle, list)]

    async def get_history(self, symbol: str, interval: str) -> list[dict[str, Any]]:
        """Fetch historical candles using an explicit provider-style method name."""
        return await self.history(symbol, interval)

    async def get_market_indices(self, instrument_keys: list[str]) -> list[dict[str, Any]]:
        """Fetch configured index quotes without inventing index identifiers."""
        if not instrument_keys:
            return []
        client = self._client()
        payload = await client.get(
            "/v2/market-quote/quotes",
            {"instrument_key": ",".join(instrument_keys)},
        )
        data = self._data(payload)
        return [value for value in data.values() if isinstance(value, dict)]
