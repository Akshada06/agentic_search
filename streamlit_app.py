import io
from typing import Any

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

API_URL = os.getenv("API_URL")
if not API_URL:
    raise ValueError(
        "API_URL environment variable not set. "
        "Set it to your deployed FastAPI backend URL."
    )
DEFAULT_MAX_ENTITIES = 8
DEFAULT_ENTITY_HINT = None


def hide_unwanted_menu_items() -> None:
    components.html(
        """
        <script>
        const HIDE_LABELS = new Set([
          "Deploy this app",
          "Deploy",
          "Record a screencast",
          "About",
          "Clear cache"
        ]);

        function hideMenuItems() {
          const rootDoc = window.parent.document;

          const allNodes = rootDoc.querySelectorAll("*");
          allNodes.forEach((node) => {
            const text = (node.innerText || "").trim();

            if (!text || !HIDE_LABELS.has(text)) return;

            const clickable =
              node.closest('[role="menuitem"]') ||
              node.closest('button') ||
              node.closest('li') ||
              node;

            if (clickable) {
              clickable.style.display = "none";
            }
          });
        }

        function observeAndHide() {
          hideMenuItems();

          const observer = new MutationObserver(() => {
            hideMenuItems();
          });

          observer.observe(window.parent.document.body, {
            childList: true,
            subtree: true,
          });
        }

        observeAndHide();
        </script>
        """,
        height=0,
        width=0,
    )


st.set_page_config(
    page_title="Agentic Search",
    page_icon="🔎",
    layout="wide",
)

hide_unwanted_menu_items()

st.title("🔎 Agentic Search")
st.caption(
    "Search the web and extract useful information with sources."
)

query = st.text_input(
    "Topic query",
)

def flatten_entities(data: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for entity in data.get("entities", []):
        row = {"entity": entity.get("entity", "")}
        row.update(entity.get("attributes", {}))
        rows.append(row)
    return pd.DataFrame(rows)


def normalize_source_items(source_info: Any) -> list[dict[str, Any]]:
    """
    Normalize different possible cell_sources formats into a clean list:
    [{"url": ..., "snippet": ..., "title": ...}, ...]
    """
    if source_info is None:
        return []

    if isinstance(source_info, dict):
        # Case 1: single source object
        if any(key in source_info for key in ["source_url", "url", "snippet", "evidence", "title"]):
            return [
                {
                    "url": source_info.get("source_url") or source_info.get("url") or "",
                    "snippet": source_info.get("snippet") or source_info.get("evidence") or "",
                    "title": source_info.get("title") or "",
                }
            ]

        # Case 2: {"sources": [...]}
        if "sources" in source_info and isinstance(source_info["sources"], list):
            normalized = []
            for item in source_info["sources"]:
                if isinstance(item, dict):
                    normalized.append(
                        {
                            "url": item.get("source_url") or item.get("url") or "",
                            "snippet": item.get("snippet") or item.get("evidence") or "",
                            "title": item.get("title") or "",
                        }
                    )
                else:
                    normalized.append({"url": "", "snippet": str(item), "title": ""})
            return normalized

        # Fallback: display key-values as a single snippet
        return [{"url": "", "snippet": str(source_info), "title": ""}]

    if isinstance(source_info, list):
        normalized = []
        for item in source_info:
            if isinstance(item, dict):
                normalized.append(
                    {
                        "url": item.get("source_url") or item.get("url") or "",
                        "snippet": item.get("snippet") or item.get("evidence") or "",
                        "title": item.get("title") or "",
                    }
                )
            else:
                normalized.append({"url": "", "snippet": str(item), "title": ""})
        return normalized

    return [{"url": "", "snippet": str(source_info), "title": ""}]


def render_clean_provenance(entity: dict[str, Any]) -> None:
    attributes = entity.get("attributes", {})
    cell_sources = entity.get("cell_sources", {})

    if not attributes:
        st.write("No extracted attributes available.")
        return

    for field, value in attributes.items():
        with st.container(border=True):
            st.markdown(f"**{field.replace('_', ' ').title()}**")
            st.write(f"Value: `{value}`")

            source_items = normalize_source_items(cell_sources.get(field))

            if not source_items:
                st.caption("No source evidence available for this field.")
                continue

            for idx, item in enumerate(source_items, start=1):
                title = item.get("title", "").strip()
                url = item.get("url", "").strip()
                snippet = item.get("snippet", "").strip()

                label = f"Source {idx}"
                if title:
                    label += f": {title}"

                if url:
                    st.markdown(f"{label}  \\n{url}")
                else:
                    st.markdown(label)

                if snippet:
                    st.caption(snippet)


if st.button("Run Search", type="primary"):
    payload = {
        "query": query,
        "max_entities": DEFAULT_MAX_ENTITIES,
        "entity_type_hint": DEFAULT_ENTITY_HINT,
    }

    with st.spinner("Searching, scraping, and extracting..."):
        try:
            response = requests.post(API_URL, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Request failed: {exc}")
            st.stop()

    entity_count = len(data.get("entities", []))
    st.success(f"Found {entity_count} entities")

    table_df = flatten_entities(data)
    if not table_df.empty:
        st.subheader("Results table")
        st.dataframe(table_df, use_container_width=True)

        csv_buffer = io.StringIO()
        table_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download CSV",
            data=csv_buffer.getvalue(),
            file_name="agentic_search_results.csv",
            mime="text/csv",
        )
    else:
        st.warning("No entities were returned for this query.")
        st.stop()

    st.subheader("Field-level provenance")
    st.caption("Each extracted value is paired with its supporting source evidence.")

    for idx, entity in enumerate(data.get("entities", []), start=1):
        entity_name = entity.get("entity", f"Entity {idx}")
        with st.expander(f"{idx}. {entity_name}", expanded=False):
            render_clean_provenance(entity)