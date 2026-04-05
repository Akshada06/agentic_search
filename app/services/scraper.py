import asyncio
from typing import Iterable, List, Optional

import httpx
from bs4 import BeautifulSoup
from readability import Document

from app.config import settings
from app.schemas import ScrapedDocument, SearchResult


class WebScraper:
    def __init__(self) -> None:
        self._headers = {"User-Agent": settings.user_agent}
        self._timeout = settings.request_timeout_seconds

    async def scrape_results(self, results: Iterable[SearchResult], limit: int) -> List[ScrapedDocument]:
        selected = list(results)[:limit]
        tasks = [self._scrape_one(result) for result in selected]
        docs = await asyncio.gather(*tasks, return_exceptions=True)
        good_docs: List[ScrapedDocument] = []
        for doc in docs:
            if isinstance(doc, ScrapedDocument) and len(doc.text) > 300:
                good_docs.append(doc)
        return good_docs

    async def _scrape_one(self, result: SearchResult) -> Optional[ScrapedDocument]:
        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers, follow_redirects=True) as client:
            resp = await client.get(result.url)
            resp.raise_for_status()
            html = resp.text

        cleaned = Document(html)
        content_html = cleaned.summary(html_partial=True)
        title = cleaned.short_title() or result.title
        soup = BeautifulSoup(content_html, "html.parser")
        text = soup.get_text(" ", strip=True)
        if not text:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

        excerpt = text[:1200]
        return ScrapedDocument(
            url=result.url,
            title=title,
            text=text[:12000],
            excerpt=excerpt,
        )
