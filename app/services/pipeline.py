from app.config import settings
from app.schemas import SearchRequest, SearchResponse
from app.services.brave_search import BraveSearchClient
from app.services.extractor import LLMExtractor
from app.services.scraper import WebScraper


class AgenticSearchPipeline:
    def __init__(self) -> None:
        self.search_client = BraveSearchClient()
        self.scraper = WebScraper()
        self.extractor = LLMExtractor()

    async def run(self, request: SearchRequest) -> SearchResponse:
        search_results = await self.search_client.search(
            query=request.query,
            count=min(settings.max_search_results, max(request.max_entities * 2, 6)),
        )
        scraped_docs = await self.scraper.scrape_results(
            search_results,
            limit=settings.max_pages_to_scrape,
        )
        return await self.extractor.extract(
            query=request.query,
            docs=scraped_docs,
            search_results=search_results,
            max_entities=request.max_entities,
            entity_type_hint=request.entity_type_hint,
        )
