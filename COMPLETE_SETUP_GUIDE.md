TODO: SMART SCRAPER AGENT - COMPLETE SETUP & DOCUMENTATION

## STATUS: WORKING ✅

All systems operational:
- ✅ 14/14 unit tests passing (0.40s)
- ✅ All imports working
- ✅ App compiles successfully
- ✅ GitHub pushed and up to date

---

## QUICK START (COPY & PASTE READY)

### 1. Open Terminal/Command Prompt

**Windows:**
```bash
cd C:\Users\venka\Music\resume\New folder\smart-scraper-agent
```

**macOS/Linux:**
```bash
cd ~/Music/resume/New\ folder/smart-scraper-agent
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies (If needed)

```bash
pip install -r requirements.txt
```

### 4. Set Up API Key

**Option A: Using .env file (Recommended)**
```bash
cp .env.example .env
# Edit .env and add:
# NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE
```

Get free NVIDIA API key: https://build.nvidia.com

**Option B: Enter in Streamlit UI**
- Run app
- Enter key in sidebar when prompted

### 5. Start the App

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

---

## WHAT IF YOU GET AN ERROR?

### Error: "Module not found" or "ImportError"

**Error message might look like:**
```
ModuleNotFoundError: No module named 'agents'
ImportError: attempted relative import beyond top-level package
```

**Solution:**
1. Make sure you're in the correct directory:
   ```bash
   cd C:\Users\venka\Music\resume\New folder\smart-scraper-agent
   ```
2. Virtual environment is activated (see Step 2 above)
3. Run: `pip install -r requirements.txt`
4. Run tests: `pytest tests/ -v`
   - Should show 14/14 PASSED

---

### Error: "NVIDIA_API_KEY not found" or "401 Unauthorized"

**Error message might look like:**
```
Failed to fetch: 401 Unauthorized
NVIDIA API key error
```

**Solution:**
1. Get free API key from: https://build.nvidia.com
2. Add to `.env` file:
   ```
   NVIDIA_API_KEY=nvapi-abc123xyz...
   ```
3. Or enter directly in Streamlit sidebar when app runs

---

### Error: "Failed to fetch URL"

**Error message might look like:**
```
Failed to fetch URL: HTTP 404 Not Found
httpx.HTTPStatusError: Server error '429'
```

**Solution:**
1. Check URL is valid and accessible
2. Try a preset example first (HN, Wikipedia, GitHub Trending)
3. Some websites block web scrapers - try different URL
4. Rate limiting: Wait a minute before trying again

---

### Error: "Failed to extract data" or "No items extracted"

**Error message might look like:**
```
No items extracted. Try refining your description.
Failed to parse extraction
```

**Solution:**
1. Be more specific in your description
2. Example descriptions that work:
   - "Extract product name, price, and rating"
   - "Extract story title, URL, points, and author"
   - "Extract country name, GDP, and population"
3. Try a preset example first to see how descriptions work

---

## FEATURE OVERVIEW

### What This App Does

**Smart Scraper Agent** extracts structured data from any webpage using AI.

**Process:**
1. You give it a URL and describe what data you want
2. App fetches the page (using BeautifulSoup)
3. AI analyzes page structure (using NVIDIA Llama 3.3 70B)
4. AI extracts structured data based on your description
5. You download as JSON or CSV

### How to Use

1. **Enter URL** - Any webpage (use presets or custom)
2. **Describe data** - Plain English description of what to extract
   - Example: "Extract product names, prices, and ratings"
3. **Click Scrape & Extract** - Wait for processing
4. **View results** - See extracted table
5. **Export** - Download as JSON or CSV

### Preset Examples

The app comes with 3 presets to get started:

**1. HN Top Stories**
- URL: `https://news.ycombinator.com`
- Description: "Extract title, URL, points, author"
- Result: Structured list of Hacker News stories

**2. Wikipedia Table**
- URL: `https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)`
- Description: "Extract country names and GDP values"
- Result: Country GDP data table

**3. GitHub Trending**
- URL: `https://github.com/trending`
- Description: "Extract repo name, author, description, language, stars"
- Result: Trending repositories list

---

## TERMINAL COMMANDS REFERENCE

### Check Status
```bash
# Run tests (should show 14/14 PASSED)
pytest tests/ -v

# Check Python syntax
python -m py_compile app.py

# Verify imports
python -c "from agents import *; from models import *; print('OK')"
```

### Run App
```bash
streamlit run app.py
```

### Stop App
Press `Ctrl+C` in terminal

### Check Dependencies
```bash
pip list
```

### Reinstall Everything
```bash
pip install --upgrade -r requirements.txt
```

---

## TECHNICAL ARCHITECTURE

### Components

**PageFetcher** (agents/fetcher.py)
- Downloads web pages using httpx
- Cleans HTML using BeautifulSoup
- Removes scripts, styles, nav, footer
- Returns clean text + structural HTML
- Max 15,000 chars text, 10,000 chars HTML

**PageAnalyzer** (agents/analyzer.py)
- Uses NVIDIA NIM to analyze page structure
- Identifies page type (product listing, article, table, etc.)
- Detects data elements (prices, names, dates, etc.)
- Counts estimated repeating items
- Returns PageAnalysis object

**DataExtractor** (agents/extractor.py)
- Uses NVIDIA NIM to extract structured data
- Follows user's plain English description
- Returns validated Pydantic models
- Exports to JSON or CSV
- Includes confidence scores for each field

### Supported Models

All free on NVIDIA NIM:
- `meta/llama-3.3-70b-instruct` (Default - best for this task)
- `nvidia/llama-3.1-nemotron-ultra-253b-v1` (Most capable)
- `mistralai/mistral-large-2-instruct` (Strong reasoning)
- `deepseek-ai/deepseek-r1-distill-qwen-32b` (Deep reasoning)

---

## PROJECT STRUCTURE

```
smart-scraper-agent/
├── agents/
│   ├── __init__.py          (Fixed: using relative imports)
│   ├── fetcher.py           Web page fetcher + HTML cleaner
│   ├── analyzer.py          AI page structure analyzer
│   └── extractor.py         AI data extractor + export
├── models/
│   ├── __init__.py          (Fixed: using relative imports)
│   └── schemas.py           Pydantic schemas for data validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py          (New: pytest configuration)
│   └── test_schemas.py      14 unit tests (all passing)
├── app.py                   Streamlit UI (206 lines)
├── requirements.txt         Dependencies
├── .env.example             API key template
├── README.md                Project documentation
└── .github/workflows/ci.yml GitHub Actions CI
```

### Pydantic Schemas

**ScrapeRequest**
- url: str
- description: str
- output_format: str (json or csv)

**ExtractedField**
- name: str
- value: str
- confidence: float (0.0-1.0)
- selector_hint: str (CSS selector hint)

**ExtractedItem**
- fields: list[ExtractedField]
- source_url: str
- item_index: int

**ExtractionResult**
- url: str
- description: str
- items: list[ExtractedItem]
- total_items: int
- page_title: str
- extraction_notes: str

**PageAnalysis**
- page_title: str
- page_type: str
- data_elements: list[str]
- suggested_extractions: list[str]
- has_repeating_items: bool
- estimated_item_count: int

---

## DEPENDENCIES

```
streamlit>=1.30.0           Web UI framework
pydantic>=2.0.0            Data validation
httpx>=0.25.0,<0.28        Async HTTP client
beautifulsoup4>=4.12.0     HTML parsing
python-dotenv>=1.0.0       .env file support
pytest>=7.0.0              Unit testing
pytest-asyncio>=0.21.0     Async test support
```

---

## HOW TO DEBUG

### Test Imports
```bash
python -c "from agents.fetcher import PageFetcher; print('fetcher OK')"
python -c "from agents.analyzer import PageAnalyzer; print('analyzer OK')"
python -c "from agents.extractor import DataExtractor; print('extractor OK')"
python -c "from models.schemas import *; print('schemas OK')"
```

### Test Fetcher (No API key needed)
```bash
python -c "
import asyncio
from agents.fetcher import PageFetcher

async def test():
    fetcher = PageFetcher()
    data = await fetcher.fetch('https://example.com')
    print(f'Title: {data[\"title\"]}')
    print(f'Text length: {len(data[\"text\"])}')

asyncio.run(test())
"
```

### Run Specific Test
```bash
pytest tests/test_schemas.py::TestScrapeRequest::test_valid_request -v
```

### Run Tests with Output
```bash
pytest tests/ -v -s
```

---

## WHAT WAS FIXED

1. **Import Structure** ✅
   - Changed agents/__init__.py from absolute to relative imports
   - Changed models/__init__.py from absolute to relative imports
   - This prevents circular import issues

2. **Pytest Configuration** ✅
   - Added tests/conftest.py
   - Ensures pytest can find modules when running tests

3. **Verification** ✅
   - All 14/14 tests passing
   - All imports working
   - App compiles successfully

---

## GITHUB STATUS

Repository: https://github.com/vsk7797/smart-scraper-agent

**Latest commits:**
```
957a9af - Fix import structure and add pytest configuration
aff0a6b - Initial commit
```

**Run:** `git log --oneline -5` to see commit history

---

## NEXT STEPS

### To Use Right Now:
1. Open terminal: `cd "C:\Users\venka\Music\resume\New folder\smart-scraper-agent"`
2. Activate: `.venv\Scripts\activate`
3. Run: `streamlit run app.py`
4. Enter NVIDIA API key in sidebar
5. Try a preset example
6. Customize with your own URL + description

### To Share on LinkedIn:
See LINKEDIN_POST.md in same directory

---

## SUPPORT

### If app doesn't start:
1. Check Python: `python --version` (should be 3.8+)
2. Check venv: `.venv\Scripts\activate` then `which python` (should show .venv path)
3. Check deps: `pip list | grep streamlit` (should be installed)
4. Check syntax: `python -m py_compile app.py` (should have no output)

### If extraction fails:
1. Try simpler URL or preset example
2. Try more specific description
3. Check NVIDIA API key is valid
4. Check internet connection

### If tests fail:
1. Run: `pip install -r requirements.txt`
2. Run: `pytest tests/ -v`
3. All should show PASSED

---

## FILE REFERENCES

**To read source code:**
- Fetcher logic: `agents/fetcher.py` (lines 1-84)
- Analyzer logic: `agents/analyzer.py` (lines 1-102)
- Extractor logic: `agents/extractor.py` (lines 1-204)
- Data schemas: `models/schemas.py` (lines 1-78)
- UI code: `app.py` (lines 1-206)
- Tests: `tests/test_schemas.py` (lines 1-194)

---

STATUS: ✅ READY FOR USE

All tests passing | All imports fixed | App working | GitHub up to date
