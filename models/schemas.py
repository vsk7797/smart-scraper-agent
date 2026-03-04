"""Pydantic schemas for Smart Scraper Agent."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """User's scraping request."""

    url: str = Field(..., description="URL to scrape")
    description: str = Field(
        ..., description="Natural language description of what data to extract"
    )
    output_format: str = Field(
        default="json", description="Output format: json or csv"
    )


class ExtractedField(BaseModel):
    """A single extracted data field."""

    name: str = Field(..., description="Field name")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the extraction"
    )
    selector_hint: str = Field(
        default="", description="CSS selector or XPath hint for the field"
    )


class ExtractedItem(BaseModel):
    """A single extracted item (e.g., one product, one listing)."""

    fields: list[ExtractedField] = Field(
        default_factory=list, description="Extracted fields for this item"
    )
    source_url: str = Field(..., description="URL the item was extracted from")
    item_index: int = Field(..., ge=0, description="Index of this item on the page")


class ExtractionResult(BaseModel):
    """Complete extraction result from a page."""

    url: str = Field(..., description="URL that was scraped")
    description: str = Field(..., description="What the user asked to extract")
    items: list[ExtractedItem] = Field(
        default_factory=list, description="Extracted items"
    )
    total_items: int = Field(..., ge=0, description="Number of items extracted")
    page_title: str = Field(default="", description="Title of the scraped page")
    extraction_notes: str = Field(
        default="", description="Notes about the extraction process"
    )


class PageAnalysis(BaseModel):
    """AI analysis of a web page's structure."""

    page_title: str = Field(default="", description="Page title")
    page_type: str = Field(
        ..., description="Type of page (e.g., product listing, article, table)"
    )
    data_elements: list[str] = Field(
        default_factory=list,
        description="Types of data elements found on the page",
    )
    suggested_extractions: list[str] = Field(
        default_factory=list,
        description="Suggested data points that can be extracted",
    )
    has_repeating_items: bool = Field(
        ..., description="Whether the page has repeating item patterns"
    )
    estimated_item_count: int = Field(
        ..., ge=0, description="Estimated number of repeating items"
    )
