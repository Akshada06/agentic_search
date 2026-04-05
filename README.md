# agentic_search

A small but production-minded agentic search system that turns an open-ended topic query into a structured entity table with traceable sources. It now includes a lightweight frontend for interactive querying, table inspection, CSV export, and raw JSON copy.

Example input:
- `AI startups in healthcare`
- `top pizza places in Brooklyn`
- `open source database tools`

Example output:
- A JSON API response
- Interactive browser UI
- Flexible inferred columns based on the topic
- Per-cell provenance with source URL and evidence snippet


## Live URLs

- **Backend API:** [https://agentic-search-eexc.onrender.com](https://agentic-search-eexc.onrender.com)  
- **Streamlit frontend:** [https://agentic-search-frontend.onrender.com](https://agentic-search-frontend.onrender.com)


## Frontend

The project includes **two ways to interact with it**:

1. **FastAPI HTML frontend** – served from `/` on the backend:
   - Query form for topic, max entities, and optional entity hint
   - Rendered structured table with expandable per-cell provenance
   - Raw JSON inspection
   - CSV export

2. **Streamlit frontend** – lightweight interactive UI:
   - Run the backend first
   - Then start Streamlit with:
     ```bash
     streamlit run streamlit_app.py
     ```
   - Open: `http://127.0.0.1:8501/` (Streamlit UI)
   - FastAPI backend HTML demo remains at `http://127.0.0.1:8000/`  
   - API docs: `http://127.0.0.1:8000/docs`

> **Note:** Streamlit app uses the environment variable `API_URL` to connect to your deployed backend:
> ```env
> API_URL=https://agentic-search-eexc.onrender.com/search
> ```


## Why this approach

The challenge is not just “search + summarize.” The goal is turning a fuzzy topic into a useful, structured entity table while keeping every cell traceable.

**Pipeline stages:**

1. **Search** – Brave Search API gathers diverse results  
2. **Scrape** – Fetch pages asynchronously and extract readable text  
3. **Extract** – OpenAI generates entities, attributes, and inferred columns  
4. **Ground** – Each returned field is linked to a source snippet  

This approach balances recall, precision and traceability.


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
- `app/templates/index.html` 
  – simple HTML frontend
- `streamlit_app.py`
  – lightweight Streamlit UI

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

Each cell is explainable because `cell_sources` stores the source URL, source title and evidence snippet for that field.

---

## Setup

### 1. Clone

```bash
git clone https://github.com/Akshada06/agentic_search.git
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

Make sure to use your actual API keys; the app will not run without them.

### 3. Install dependencies

Create and activate a Python virtual environment, then install packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the backend locally

```bash
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` for the interactive frontend
- `http://127.0.0.1:8000/docs` for the API docs

Run the Streamlit frontend:

```bash
streamlit run streamlit_app.py
```

Open:
- `http://127.0.0.1:8501/` 

## Run on a Mac without cloning

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

---

## Design decisions and trade-offs

The system is designed to balance flexibility, traceability, and efficiency. Key decisions and their trade-offs:

### 1. Flexible schema (LLM-inferred columns)
Instead of a fixed schema the system lets the LLM infer the most useful columns per query.  
- Works well across diverse topics like restaurants, startups, or open-source tools.  
- Columns are returned in `inferred_columns` for structured output.

**Trade-off:** Column consistency across unrelated queries may vary. Domain-specific templates could improve this in future versions.

### 2. Per-cell provenance
Every field includes a source object with URL, title and evidence snippet.  
- Supports traceability and transparency for each extracted value.  

**Trade-off:** Increases response payload size but improves trust and debuggability.

### 3. Async scraping with readability-lxml
Pages are fetched asynchronously and HTML is cleaned to remove noise (navbars, ads, headers).  
- Ensures faster scraping and cleaner input for extraction.

**Trade-off:** Some dynamic or client-rendered pages may not be fully captured. Browser automation could improve this in future versions.

### 4. Single extraction pass
The pipeline performs one extraction pass after scraping.  
- Keeps latency and API costs low.  

**Trade-off:** Limits advanced processing like query expansion, re-ranking, source scoring, entity reconciliation or verification. Future improvements could add these stages for higher quality output.

---

## Known limitations

- Some pages block scraping or require JavaScript rendering.
- Extraction quality depends on the sources retrieved.
- No browser automation yet for dynamic websites.
- No persistent cache or database.
- No evaluation harness included.

---

## Repo structure

```agentic_search/
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

