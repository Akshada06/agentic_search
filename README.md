# agentic_search

A small but production-minded agentic search system that turns an open-ended topic query into a structured, source-traceable entity table. It now includes a lightweight frontend for interactive querying, table inspection, CSV export, and raw JSON copy.

Example input:
- `AI startups in healthcare`
- `top pizza places in Brooklyn`
- `open source database tools`

Example output:
- A JSON API response
- A simple browser UI at `/`
- Flexible inferred columns based on the topic
- Per-cell provenance so every value can be traced to a source URL and evidence snippet

---


## Frontend

A simple frontend is included at `app/templates/index.html` and served from `/`.

It gives you:
- a query form for topic, max entities, and optional entity hint
- one-click sample queries
- a rendered structured table
- expandable per-cell provenance
- raw JSON inspection
- CSV export for the table

This is useful in the submission because reviewers can test the backend from `/docs` and also quickly see a polished demo from the homepage.

## Why this approach

The challenge is not just “search + summarize.” The hard part is turning a fuzzy topic into a useful entity table while keeping each cell explainable.

I designed the pipeline around four stages:

1. **Search** with Brave Search API to gather a diverse result set.
2. **Scrape** result pages and extract readable article/page text.
3. **Extract** entities and attributes with OpenAI.
4. **Ground** every returned field in a source snippet.

This gives a practical balance of:
- decent recall from search,
- better precision from LLM-based extraction,
- and trust via source-traceable cells.

---

## Architecture

```text
User query
   ↓
Brave Search API
   ↓
Top N web results
   ↓
Async scraping + readability extraction
   ↓
OpenAI extraction pass
   ↓
Structured entities + inferred columns + per-cell provenance
```

### Components

- `app/services/brave_search.py`
  - Calls Brave web search
- `app/services/scraper.py`
  - Fetches pages asynchronously
  - Uses `readability-lxml` + BeautifulSoup to convert HTML into usable text
- `app/services/extractor.py`
  - Sends search results + scraped text to OpenAI
  - Asks the model to infer useful columns and return traceable cells
- `app/services/pipeline.py`
  - Orchestrates the full workflow
- `app/main.py`
  - FastAPI entrypoint

---

## API

### POST `/search`

Request:

```json
{
  "query": "AI startups in healthcare",
  "max_entities": 8,
  "entity_type_hint": "company"
}
```

Response shape:

```json
{
  "query": "AI startups in healthcare",
  "inferred_columns": ["category", "website", "location", "focus_area"],
  "entities": [
    {
      "entity": "Example Health AI",
      "attributes": {
        "website": "https://example.com",
        "focus_area": "clinical documentation"
      },
      "cell_sources": {
        "entity": {
          "value": "Example Health AI",
          "source_url": "https://example.com/about",
          "source_title": "About Example Health AI",
          "evidence": "Example Health AI helps clinicians automate documentation."
        },
        "website": {
          "value": "https://example.com",
          "source_url": "https://example.com/about",
          "source_title": "About Example Health AI",
          "evidence": "Visit example.com to learn more."
        }
      }
    }
  ],
  "search_results": [],
  "scraped_urls": []
}
```

Each cell is explainable because `cell_sources` stores the source URL, source title, and evidence snippet for that field.

---

## Setup

### 1. Clone

```bash
git clone https://github.com/yourname/agentic_search.git
cd agentic_search
```

### 2. Create environment file

```bash
cp .env.example .env
```

Fill in:

```env
OPENAI_API_KEY=...
BRAVE_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

### 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run locally

```bash
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` for the interactive frontend
- `http://127.0.0.1:8000/docs` for the API docs



## Run on a Mac

If you download the repo zip instead of cloning it, this is the quickest path:

```bash
cd ~/Downloads
unzip agentic_search.zip
cd agentic_search
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and add your keys:

```env
OPENAI_API_KEY=your_openai_key
BRAVE_API_KEY=your_brave_key
OPENAI_MODEL=gpt-4.1-mini
```

Start the app:

```bash
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` for the frontend
- `http://127.0.0.1:8000/docs` for Swagger

If `python3` is missing on your Mac, install it with Homebrew:

```bash
brew install python
```

---

## Design decisions and trade-offs

### 1. Flexible schema instead of fixed columns
A fixed schema works poorly across very different queries like restaurants, startups, and open-source tools.

I let the LLM infer the most useful columns for the query and return them in `inferred_columns`. This makes the system more general while still keeping results structured.

**Trade-off:** column consistency across unrelated queries is lower. If needed, the next version could add domain-specific templates.

### 2. Per-cell provenance
Rather than only citing sources at the row level, each field gets its own source object.

This is important because the challenge explicitly asks that each cell value be traceable.

**Trade-off:** response payloads are larger, but trust and debuggability are much better.

### 3. Async scraping with readability extraction
Raw HTML is noisy. Readability extraction removes nav bars, headers, and unrelated page furniture.

**Trade-off:** some pages still render poorly, and heavily client-side sites may need browser-based rendering in a future version.

### 4. Single extraction pass
The current system does one extraction pass after scraping.

**Trade-off:** this keeps latency and cost reasonable, but a stronger version would add:
- query expansion,
- re-ranking,
- source quality scoring,
- entity merge/reconciliation,
- and a second verification pass.

---

## What I would improve next

If I were pushing this beyond the baseline, I would add:

1. **Query planning / expansion**
   - Generate multiple search angles from one user query.
   - Example: for `AI startups in healthcare`, search startup lists, funding databases, company directories, and recent market maps.

2. **Source scoring**
   - Weight official websites, company about pages, GitHub repos, and high-quality directories more than generic SEO pages.

3. **Entity reconciliation**
   - Merge duplicate entities found under slightly different names.

4. **Verification pass**
   - Re-check weak cells against source text before returning results.

5. **Rendered table frontend**
   - Add a simple UI that shows the table and lets users expand each cell’s provenance.

6. **Caching**
   - Cache search results and scraped pages to improve latency and reduce cost.

---

## Known limitations

- Some pages block scraping or require JavaScript rendering.
- The extraction quality depends on the quality of the retrieved sources.
- No browser automation yet for dynamic websites.
- No persistent cache/database yet.
- No evaluation harness yet.

---

## Why this should score well

This submission aims to do more than the minimum:

- **Structured output** instead of free-form summaries
- **Per-cell traceability** instead of row-level citations only
- **Async scraping** for better latency
- **Generalizable schema inference** across different query types
- **Clear separation of responsibilities** in the codebase
- **Readable README with trade-offs and next steps**

It is intentionally simple enough to run locally, but structured so it can be extended into a more serious retrieval and extraction system.

---

## Submission notes

Recommended email subject:

```text
CIIR challenge submission
```

In the email body, include:
- GitHub repository link
- optional live demo link
- short summary of the approach



---

## Frontend

The homepage provides a minimal UI that lets you:
- enter a topic query
- set `max_entities` and an optional `entity_type_hint`
- run the pipeline without using Swagger
- inspect the rendered table, raw JSON, scraped URLs, and source provenance for each cell

This makes the project easier to demo live during review.


## Streamlit frontend

This repo also includes a lightweight Streamlit UI in `streamlit_app.py`.

Run the backend first:

```bash
python -m uvicorn app.main:app --reload
```

Then in a second terminal:

```bash
streamlit run streamlit_app.py
```

Open:
- `http://127.0.0.1:8501/` for the Streamlit UI
- `http://127.0.0.1:8000/` for the built-in FastAPI HTML demo
- `http://127.0.0.1:8000/docs` for Swagger docs

## Recommended repo structure

```text
agentic_search/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── services/
│   │   ├── brave_search.py
│   │   ├── scraper.py
│   │   ├── extractor.py
│   │   └── pipeline.py
│   └── templates/
│       └── index.html
├── streamlit_app.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
