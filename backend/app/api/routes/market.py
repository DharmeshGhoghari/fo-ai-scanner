from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api/market", tags=["market"])

_INDEXES = (
    {"symbol": "NIFTY50", "name": "NIFTY 50"},
    {"symbol": "SENSEX", "name": "SENSEX"},
    {"symbol": "BANKNIFTY", "name": "BANK NIFTY"},
    {"symbol": "INDIAVIX", "name": "INDIA VIX"},
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/status")
async def market_status() -> dict[str, object]:
    """Return market metadata without inventing live exchange values."""
    return {
        "market_open": False,
        "exchange": "NSE/BSE",
        "timezone": "Asia/Kolkata",
        "last_updated": _utc_timestamp(),
        "status": "API_NOT_CONFIGURED",
        "provider": "upstox" if settings.upstox_access_token else None,
    }


@router.get("/indices")
async def market_indices() -> dict[str, list[dict[str, str]]]:
    """Return index identities until a configured Upstox provider supplies observations."""
    return {
        "indices": [
            {
                "symbol": index["symbol"],
                "name": index["name"],
                "status": "API_NOT_CONFIGURED",
            }
            for index in _INDEXES
        ]
    }
