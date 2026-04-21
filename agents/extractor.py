"""Data extractor — uses AI to extract structured data from web page content."""

from __future__ import annotations

import csv
import io
import json
import os

import httpx

from models.schemas import (
    ExtractedField,
    ExtractedItem,
    ExtractionResult,
    PageAnalysis,
)

NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"


class DataExtractor:
    """Extracts structured data from web pages using NVIDIA NIM LLM."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")

    async def extract(
        self,
        page_data: dict,
        description: str,
        analysis: PageAnalysis | None = None,
    ) -> ExtractionResult:
        """Extract data from a page based on the user's description."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(page_data, description, analysis)

        raw = await self._call_llm(system_prompt, user_prompt)
        return self._parse_result(raw, page_data["url"], description, page_data["title"])

    def to_json(self, result: ExtractionResult) -> str:
        """Convert extraction result to JSON string."""
        items = []
        for item in result.items:
            row = {}
            for field in item.fields:
                row[field.name] = field.value
            items.append(row)
        return json.dumps(items, indent=2, ensure_ascii=False)

    def to_csv(self, result: ExtractionResult) -> str:
        """Convert extraction result to CSV string."""
        if not result.items:
            return ""

        # Collect all unique field names
        field_names: list[str] = []
        for item in result.items:
            for field in item.fields:
                if field.name not in field_names:
                    field_names.append(field.name)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=field_names)
        writer.writeheader()
        for item in result.items:
            row = {f.name: f.value for f in item.fields}
            writer.writerow(row)
        return output.getvalue()

    # ── Prompt construction ─────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        return (
            "You are a precise web data extractor. Given a web page's content and a user's "
            "description of what to extract, return the extracted data as VALID JSON only.\n\n"
            "IMPORTANT: Return ONLY valid JSON, no other text before or after.\n\n"
            "Response format (must be valid JSON):\n"
            "{\n"
            '  "items": [\n'
            "    {\n"
            '      "fields": [\n'
            '        {"name": "field_name", "value": "extracted_value", "confidence": 0.95}\n'
            "      ]\n"
            "    }\n"
            "  ],\n"
            '  "extraction_notes": "Summary of what was extracted"\n'
            "}\n\n"
            "Rules:\n"
            "1. Return ONLY valid JSON, nothing else\n"
            "2. Extract ONLY the data described by the user\n"
            "3. Keep field names clean and consistent across items\n"
            "4. Set confidence 0-1 based on how certain you are about each value\n"
            "5. If a field is not found for an item, omit it from that item\n"
            "6. Return an empty items list [] if no matching data is found\n"
            "7. Do not include any markdown, code blocks, or explanation\n"
            "8. Ensure the JSON is properly formatted and valid"
        )

    def _build_user_prompt(
        self,
        page_data: dict,
        description: str,
        analysis: PageAnalysis | None,
    ) -> str:
        parts = [
            f"URL: {page_data['url']}",
            f"Page Title: {page_data['title']}",
            f"\nUSER REQUEST: {description}",
        ]

        if analysis:
            parts.append(
                f"\nPAGE ANALYSIS:\n"
                f"- Type: {analysis.page_type}\n"
                f"- Data elements: {', '.join(analysis.data_elements)}\n"
                f"- Has repeating items: {analysis.has_repeating_items}\n"
                f"- Est. items: {analysis.estimated_item_count}"
            )

        parts.append(f"\nPAGE CONTENT:\n{page_data['text'][:8000]}")

        if page_data.get("html_snippet"):
            parts.append(f"\nHTML STRUCTURE:\n{page_data['html_snippet'][:4000]}")

        return "\n".join(parts)

    # ── LLM call ────────────────────────────────────────────────────
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
            "max_tokens": 4096,
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(NVIDIA_NIM_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ── Response parsing ────────────────────────────────────────────
    def _parse_result(
        self, raw: str, url: str, description: str, title: str
    ) -> ExtractionResult:
        try:
            text = self._extract_json(raw)
            
            # Try to parse JSON
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return error with details
                return ExtractionResult(
                    url=url,
                    description=description,
                    items=[],
                    total_items=0,
                    page_title=title,
                    extraction_notes=f"JSON parsing failed. Raw response: {raw[:300]}",
                )

            items: list[ExtractedItem] = []
            for i, raw_item in enumerate(data.get("items", [])):
                fields = []
                for f in raw_item.get("fields", []):
                    try:
                        confidence = float(f.get("confidence", 0.5))
                        confidence = max(0.0, min(1.0, confidence))
                    except (ValueError, TypeError):
                        confidence = 0.5
                    
                    fields.append(
                        ExtractedField(
                            name=str(f.get("name", "unknown")),
                            value=str(f.get("value", "")),
                            confidence=confidence,
                            selector_hint=str(f.get("selector_hint", "")),
                        )
                    )
                if fields:  # Only add item if it has fields
                    items.append(
                        ExtractedItem(fields=fields, source_url=url, item_index=i)
                    )

            return ExtractionResult(
                url=url,
                description=description,
                items=items,
                total_items=len(items),
                page_title=title,
                extraction_notes=data.get("extraction_notes", ""),
            )
        except Exception as e:
            # Catch any other unexpected errors
            return ExtractionResult(
                url=url,
                description=description,
                items=[],
                total_items=0,
                page_title=title,
                extraction_notes=f"Extraction failed: {str(e)[:200]}",
            )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text, handling markdown code blocks and other formats."""
        text = text.strip()
        
        # Handle markdown code blocks (```json ... ```)
        if text.startswith("```"):
            lines = text.split("\n")
            # Find first ``` line
            start = 0
            # Skip language identifier if present (e.g., ```json)
            if lines[0].startswith("```"):
                start = 1
            
            # Find closing ```
            end = len(lines)
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip().startswith("```"):
                    end = i
                    break
            
            text = "\n".join(lines[start:end]).strip()
        
        # Handle case where JSON might be wrapped in other text
        # Try to find the JSON object/array
        if not text.startswith(("{", "[")):
            # Look for first { or [
            for i, char in enumerate(text):
                if char in ("{", "["):
                    text = text[i:]
                    break
        
        return text.strip()
