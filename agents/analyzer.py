"""Page analyzer — uses AI to understand page structure and suggest extractions."""

from __future__ import annotations

import json
import os

import httpx

from models.schemas import PageAnalysis

NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"


class PageAnalyzer:
    """Analyzes a web page's structure using NVIDIA NIM LLM."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")

    async def analyze(self, page_data: dict) -> PageAnalysis:
        """Analyze a fetched page and return structured analysis."""
        system_prompt = (
            "You are a web page analyst. Given the text content and HTML structure of a web page, "
            "analyze it and respond in JSON with these keys:\n"
            "- page_type: string (e.g., 'product listing', 'article', 'table data', 'directory', 'search results')\n"
            "- data_elements: list of strings (types of data found, e.g., 'prices', 'names', 'dates')\n"
            "- suggested_extractions: list of strings (specific data points that could be extracted)\n"
            "- has_repeating_items: boolean (whether there are repeating patterns like product cards)\n"
            "- estimated_item_count: integer (how many repeating items are on the page)\n"
        )
        user_prompt = (
            f"URL: {page_data['url']}\n"
            f"Title: {page_data['title']}\n\n"
            f"PAGE TEXT (first 5000 chars):\n{page_data['text'][:5000]}\n\n"
            f"HTML STRUCTURE:\n{page_data['html_snippet'][:3000]}"
        )

        raw = await self._call_llm(system_prompt, user_prompt)
        return self._parse_analysis(raw, page_data["title"])

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(NVIDIA_NIM_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _parse_analysis(self, raw: str, title: str) -> PageAnalysis:
        try:
            text = self._extract_json(raw)
            data = json.loads(text)
            return PageAnalysis(
                page_title=title,
                page_type=data.get("page_type", "unknown"),
                data_elements=data.get("data_elements", []),
                suggested_extractions=data.get("suggested_extractions", []),
                has_repeating_items=bool(data.get("has_repeating_items", False)),
                estimated_item_count=max(0, int(data.get("estimated_item_count", 0))),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return PageAnalysis(
                page_title=title,
                page_type="unknown",
                data_elements=[],
                suggested_extractions=[],
                has_repeating_items=False,
                estimated_item_count=0,
            )

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            start = 1
            end = len(lines)
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip().startswith("```"):
                    end = i
                    break
            text = "\n".join(lines[start:end])
        return text.strip()
