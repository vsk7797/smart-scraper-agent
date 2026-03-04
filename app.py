"""Smart Scraper Agent — Streamlit application."""

import asyncio
import streamlit as st

from agents.fetcher import PageFetcher
from agents.analyzer import PageAnalyzer
from agents.extractor import DataExtractor

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Scraper Agent",
    page_icon="🕷️",
    layout="wide",
)

st.title("🕷️ Smart Scraper Agent")
st.markdown(
    "Give a **URL** and describe what data you want — the AI analyzes the page, "
    "extracts structured data, and exports to **JSON or CSV**."
)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    nvidia_key = st.text_input(
        "NVIDIA NIM API Key",
        type="password",
        help="Free key from https://build.nvidia.com",
    )

    st.divider()
    st.subheader("Model")
    model = st.selectbox(
        "LLM Model",
        [
            "meta/llama-3.3-70b-instruct",
            "nvidia/llama-3.1-nemotron-ultra-253b-v1",
            "mistralai/mistral-large-2-instruct",
            "deepseek-ai/deepseek-r1-distill-qwen-32b",
        ],
    )

    st.divider()
    st.subheader("Output Format")
    output_format = st.radio("Export as", ["JSON", "CSV"])


# ── Helper ──────────────────────────────────────────────────────────
def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Preset examples ─────────────────────────────────────────────────
PRESETS = {
    "Custom": {"url": "", "desc": ""},
    "HN Top Stories": {
        "url": "https://news.ycombinator.com",
        "desc": "Extract the title, URL, points, and author for each story on the front page",
    },
    "Wikipedia Table": {
        "url": "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)",
        "desc": "Extract country names and GDP values from the main data table",
    },
    "GitHub Trending": {
        "url": "https://github.com/trending",
        "desc": "Extract repository name, author, description, language, and stars for each trending repo",
    },
}

# ── Main area ───────────────────────────────────────────────────────
st.header("1. Define Scraping Task")

preset = st.selectbox("Preset examples", list(PRESETS.keys()))
preset_data = PRESETS[preset]

url = st.text_input(
    "URL to scrape",
    value=preset_data["url"],
    placeholder="https://example.com/products",
)

description = st.text_area(
    "What data do you want to extract?",
    value=preset_data["desc"],
    height=100,
    placeholder="Extract product names, prices, ratings, and availability...",
)

# ── Run extraction ──────────────────────────────────────────────────
if url.strip() and description.strip() and nvidia_key:
    if st.button("🚀 Scrape & Extract", type="primary"):
        fetcher = PageFetcher()
        analyzer = PageAnalyzer(model=model, api_key=nvidia_key)
        extractor = DataExtractor(model=model, api_key=nvidia_key)

        # Step 1: Fetch page
        st.header("2. Pipeline Progress")
        with st.spinner("Fetching page..."):
            try:
                page_data = run_async(fetcher.fetch(url))
                st.success(
                    f"Fetched: **{page_data['title'] or url}** "
                    f"({len(page_data['text']):,} chars)"
                )
            except Exception as e:
                st.error(f"Failed to fetch URL: {e}")
                st.stop()

        # Step 2: Analyze page
        with st.spinner("Analyzing page structure..."):
            analysis = run_async(analyzer.analyze(page_data))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Page Analysis")
            st.markdown(f"**Type:** {analysis.page_type}")
            st.markdown(f"**Repeating items:** {'Yes' if analysis.has_repeating_items else 'No'}")
            st.markdown(f"**Estimated items:** {analysis.estimated_item_count}")
        with col2:
            if analysis.data_elements:
                st.subheader("Data Elements Found")
                for elem in analysis.data_elements:
                    st.markdown(f"- {elem}")
            if analysis.suggested_extractions:
                st.subheader("Suggested Extractions")
                for sug in analysis.suggested_extractions:
                    st.markdown(f"- {sug}")

        # Step 3: Extract data
        with st.spinner("Extracting structured data..."):
            result = run_async(extractor.extract(page_data, description, analysis))

        # Step 4: Display results
        st.header("3. Extracted Data")

        if result.total_items == 0:
            st.warning("No items extracted. Try refining your description.")
        else:
            st.success(f"Extracted **{result.total_items}** items")

            if result.extraction_notes:
                st.info(f"Notes: {result.extraction_notes}")

            # Show as table
            table_data = []
            for item in result.items:
                row = {}
                for field in item.fields:
                    row[field.name] = field.value
                table_data.append(row)

            if table_data:
                st.dataframe(table_data, use_container_width=True)

            # Export
            st.header("4. Export")

            if output_format == "JSON":
                json_str = extractor.to_json(result)
                st.code(json_str, language="json")
                st.download_button(
                    "📥 Download JSON",
                    data=json_str,
                    file_name="extracted_data.json",
                    mime="application/json",
                )
            else:
                csv_str = extractor.to_csv(result)
                st.code(csv_str)
                st.download_button(
                    "📥 Download CSV",
                    data=csv_str,
                    file_name="extracted_data.csv",
                    mime="text/csv",
                )

            # Detailed view
            with st.expander("🔍 Detailed Item View"):
                for i, item in enumerate(result.items):
                    st.markdown(f"**Item {i + 1}:**")
                    for field in item.fields:
                        conf_color = "green" if field.confidence >= 0.8 else "orange" if field.confidence >= 0.5 else "red"
                        st.markdown(
                            f"- **{field.name}:** {field.value} "
                            f"(:{conf_color}[{field.confidence:.0%}])"
                        )
                    st.divider()

elif not nvidia_key:
    st.info("Enter your NVIDIA NIM API key in the sidebar to get started.")
elif not url.strip():
    st.info("Enter a URL to scrape.")
elif not description.strip():
    st.info("Describe what data you want to extract.")

# ── Footer ──────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built with PydanticAI patterns · NVIDIA NIM (Llama 3.3 70B) · BeautifulSoup · Streamlit"
)
