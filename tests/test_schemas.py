"""Tests for Smart Scraper Agent schemas and components."""

import pytest
from models.schemas import (
    ScrapeRequest,
    ExtractedField,
    ExtractedItem,
    ExtractionResult,
    PageAnalysis,
)


# ── ScrapeRequest tests ────────────────────────────────────────────
class TestScrapeRequest:
    def test_valid_request(self):
        req = ScrapeRequest(
            url="https://example.com",
            description="Extract product names and prices",
        )
        assert req.output_format == "json"

    def test_csv_format(self):
        req = ScrapeRequest(
            url="https://example.com",
            description="Extract data",
            output_format="csv",
        )
        assert req.output_format == "csv"


# ── ExtractedField tests ──────────────────────────────────────────
class TestExtractedField:
    def test_valid_field(self):
        field = ExtractedField(
            name="price",
            value="$29.99",
            confidence=0.95,
        )
        assert field.name == "price"
        assert field.selector_hint == ""

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            ExtractedField(name="x", value="y", confidence=1.5)

    def test_with_selector(self):
        field = ExtractedField(
            name="title",
            value="Product A",
            confidence=0.9,
            selector_hint=".product-title",
        )
        assert field.selector_hint == ".product-title"


# ── ExtractedItem tests ───────────────────────────────────────────
class TestExtractedItem:
    def test_valid_item(self):
        item = ExtractedItem(
            fields=[
                ExtractedField(name="name", value="Widget", confidence=0.9),
                ExtractedField(name="price", value="$10", confidence=0.85),
            ],
            source_url="https://example.com",
            item_index=0,
        )
        assert len(item.fields) == 2
        assert item.item_index == 0

    def test_empty_fields(self):
        item = ExtractedItem(
            fields=[],
            source_url="https://example.com",
            item_index=0,
        )
        assert item.fields == []


# ── ExtractionResult tests ────────────────────────────────────────
class TestExtractionResult:
    def test_valid_result(self):
        result = ExtractionResult(
            url="https://example.com",
            description="Extract products",
            items=[],
            total_items=0,
            page_title="Example",
        )
        assert result.total_items == 0

    def test_with_items(self):
        item = ExtractedItem(
            fields=[ExtractedField(name="title", value="Test", confidence=0.9)],
            source_url="https://example.com",
            item_index=0,
        )
        result = ExtractionResult(
            url="https://example.com",
            description="Extract titles",
            items=[item],
            total_items=1,
            page_title="Test Page",
            extraction_notes="Found 1 item",
        )
        assert result.total_items == 1
        assert result.extraction_notes == "Found 1 item"


# ── PageAnalysis tests ────────────────────────────────────────────
class TestPageAnalysis:
    def test_valid_analysis(self):
        analysis = PageAnalysis(
            page_title="Products",
            page_type="product listing",
            data_elements=["prices", "names", "ratings"],
            suggested_extractions=["product name", "price", "rating"],
            has_repeating_items=True,
            estimated_item_count=20,
        )
        assert analysis.has_repeating_items is True
        assert analysis.estimated_item_count == 20

    def test_minimal_analysis(self):
        analysis = PageAnalysis(
            page_type="article",
            has_repeating_items=False,
            estimated_item_count=0,
        )
        assert analysis.page_title == ""
        assert analysis.data_elements == []


# ── DataExtractor export tests ────────────────────────────────────
class TestDataExtractorExports:
    def _make_result(self):
        items = [
            ExtractedItem(
                fields=[
                    ExtractedField(name="name", value="Widget A", confidence=0.9),
                    ExtractedField(name="price", value="$10", confidence=0.85),
                ],
                source_url="https://example.com",
                item_index=0,
            ),
            ExtractedItem(
                fields=[
                    ExtractedField(name="name", value="Widget B", confidence=0.88),
                    ExtractedField(name="price", value="$20", confidence=0.92),
                ],
                source_url="https://example.com",
                item_index=1,
            ),
        ]
        return ExtractionResult(
            url="https://example.com",
            description="Extract products",
            items=items,
            total_items=2,
            page_title="Test",
        )

    def test_to_json(self):
        from agents.extractor import DataExtractor
        import json

        extractor = DataExtractor.__new__(DataExtractor)
        result = self._make_result()
        json_str = extractor.to_json(result)
        data = json.loads(json_str)
        assert len(data) == 2
        assert data[0]["name"] == "Widget A"
        assert data[1]["price"] == "$20"

    def test_to_csv(self):
        from agents.extractor import DataExtractor

        extractor = DataExtractor.__new__(DataExtractor)
        result = self._make_result()
        csv_str = extractor.to_csv(result)
        assert "name" in csv_str
        assert "Widget A" in csv_str
        assert "Widget B" in csv_str

    def test_empty_csv(self):
        from agents.extractor import DataExtractor

        extractor = DataExtractor.__new__(DataExtractor)
        result = ExtractionResult(
            url="https://example.com",
            description="test",
            items=[],
            total_items=0,
        )
        assert extractor.to_csv(result) == ""
