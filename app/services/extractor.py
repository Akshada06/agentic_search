import json
from typing import List

from openai import AsyncOpenAI

from app.config import settings
from app.schemas import EntityRow, ScrapedDocument, SearchResponse, SearchResult


SYSTEM_PROMPT = """
You extract structured entities from noisy web pages.

Requirements:
- Infer the most useful output columns for the query.
- Return up to the requested number of entities.
- Deduplicate near-duplicate entities.
- Every field must be traceable to a single source snippet from the provided documents.
- Only use evidence explicitly present in the provided documents.
- If a value is unknown, omit the field instead of guessing.
- Prefer primary sources or strong directory/list pages when available.
- Return valid JSON matching the requested schema.
""".strip()


class LLMExtractor:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def extract(
        self,
        query: str,
        docs: List[ScrapedDocument],
        search_results: List[SearchResult],
        max_entities: int,
        entity_type_hint: str | None,
    ) -> SearchResponse:
        docs_payload = [
            {
                "url": d.url,
                "title": d.title,
                "excerpt": d.excerpt,
                "text": d.text,
            }
            for d in docs
        ]
        results_payload = [r.model_dump() for r in search_results]

        user_prompt = f"""
Query: {query}
Entity type hint: {entity_type_hint or 'none'}
Max entities: {max_entities}

Search results:
{json.dumps(results_payload, ensure_ascii=False, indent=2)}

Scraped documents:
{json.dumps(docs_payload, ensure_ascii=False, indent=2)}

Return JSON with this exact top-level shape:
{{
  "query": str,
  "inferred_columns": [str, ...],
  "entities": [
    {{
      "entity": str,
      "attributes": {{"column_name": value, ...}},
      "cell_sources": {{
        "entity": {{"value": str, "source_url": str, "source_title": str, "evidence": str}},
        "column_name": {{"value": any, "source_url": str, "source_title": str, "evidence": str}}
      }}
    }}
  ],
  "search_results": [{{"title": str, "url": str, "description": str | null, "source": str}}],
  "scraped_urls": [str, ...]
}}

Rules:
- Each entity must also include source for the entity name itself under cell_sources.entity.
- inferred_columns should reflect the union of useful columns across entities.
- Keep evidence short and verbatim when possible, at most 220 characters.
- Only include attributes that are supported by evidence.
- Sort entities by overall usefulness for the query.
""".strip()

        response = await self.client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        text = response.output_text
        parsed = json.loads(text)
        return SearchResponse(
            query=parsed["query"],
            inferred_columns=parsed["inferred_columns"],
            entities=[EntityRow.model_validate(entity) for entity in parsed["entities"]],
            search_results=[SearchResult.model_validate(item) for item in parsed["search_results"]],
            scraped_urls=parsed["scraped_urls"],
        )
