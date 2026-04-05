from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="Topic query, e.g. 'AI startups in healthcare'")
    max_entities: int = Field(default=10, ge=1, le=30)
    entity_type_hint: Optional[str] = Field(
        default=None,
        description="Optional hint such as company, restaurant, tool, project, school",
    )


class SearchResult(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    source: str = "brave"


class ScrapedDocument(BaseModel):
    url: str
    title: str
    text: str
    excerpt: str


class CellSource(BaseModel):
    value: Any
    source_url: str
    source_title: str
    evidence: str


class EntityRow(BaseModel):
    entity: str
    attributes: Dict[str, Any]
    cell_sources: Dict[str, CellSource]


class SearchResponse(BaseModel):
    query: str
    inferred_columns: List[str]
    entities: List[EntityRow]
    search_results: List[SearchResult]
    scraped_urls: List[str]
