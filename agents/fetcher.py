"""Page fetcher — downloads web pages and cleans HTML for AI processing."""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup


class PageFetcher:
    """Fetches web pages and extracts clean text + structural HTML."""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    async def fetch(self, url: str) -> dict:
        """Fetch a URL and return cleaned content.

        Returns dict with keys: url, title, text, html_snippet, status_code
        """
        headers = {"User-Agent": self.USER_AGENT}

        async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True
        ) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, and nav elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = self._clean_text(soup.get_text())

        # Keep a truncated version of structural HTML for the AI
        html_snippet = self._extract_structural_html(soup)

        return {
            "url": url,
            "title": title,
            "text": text[:15000],  # Cap to avoid token limits
            "html_snippet": html_snippet[:10000],
            "status_code": resp.status_code,
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove very long runs of special chars
        text = re.sub(r"[^\w\s.,;:!?@#$%&*()\-+=\[\]{}<>/\\|\"']{5,}", "", text)
        return text.strip()

    @staticmethod
    def _extract_structural_html(soup: BeautifulSoup) -> str:
        """Extract key structural elements (tables, lists, main content divs)."""
        parts: list[str] = []

        # Tables
        for table in soup.find_all("table")[:3]:
            parts.append(str(table))

        # Lists
        for lst in soup.find_all(["ul", "ol"])[:5]:
            parts.append(str(lst))

        # Main content areas
        main = soup.find("main") or soup.find("article") or soup.find("div", {"class": re.compile(r"content|main|body", re.I)})
        if main:
            parts.append(str(main)[:5000])

        if not parts:
            # Fallback: take the body
            body = soup.find("body")
            if body:
                parts.append(str(body)[:5000])

        return "\n".join(parts)
