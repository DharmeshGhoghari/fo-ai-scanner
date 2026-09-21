from app.config import settings
from app.providers.base import NewsProvider, ProviderNotConfigured

class NewsAPISource(NewsProvider):
    async def search(self, query: str) -> list[dict]:
        if not settings.news_api_key: raise ProviderNotConfigured('NEWS_API_KEY is not configured')
        return []

class GNewsSource(NewsProvider):
    async def search(self, query: str) -> list[dict]:
        if not settings.gnews_api_key: raise ProviderNotConfigured('GNEWS_API_KEY is not configured')
        return []
