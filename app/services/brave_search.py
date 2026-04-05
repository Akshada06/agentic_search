from typing import List

import httpx

from app.config import settings
from app.schemas import SearchResult


BRAVE_WEB_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchClient:
    async def search(self, query: str, count: int) -> List[SearchResult]:
        headers = {
            "X-Subscription-Token": settings.brave_api_key,
            "Accept": "application/json",
        }
        params = {
            "q": query,
            "count": count,
            "search_lang": "en",
            "safesearch": "moderate",
        }
        timeout = settings.request_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.get(BRAVE_WEB_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    description=item.get("description"),
                    source="brave",
                )
            )
        return results
