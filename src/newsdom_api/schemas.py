"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(
        ...,
        description="Leftmost X coordinate of the bounding box.",
        json_schema_extra={"example": 45.5},
    )
    y0: float = Field(
        ...,
        description="Topmost Y coordinate of the bounding box.",
        json_schema_extra={"example": 100.0},
    )
    x1: float = Field(
        ...,
        description="Rightmost X coordinate of the bounding box.",
        json_schema_extra={"example": 250.5},
    )
    y1: float = Field(
        ...,
        description="Bottommost Y coordinate of the bounding box.",
        json_schema_extra={"example": 300.0},
    )


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(
        ...,
        description="Text content of the caption.",
        json_schema_extra={"example": "Figure 1. Market trends."},
    )
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description="Bounding box of the caption when parser coordinates are available.",
    )


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(
        ...,
        description="Relative path to the extracted image asset.",
        json_schema_extra={"example": "images/page1_img1.jpg"},
    )
    media_type: str = Field(
        default="image",
        description="Media type label for the extracted image node.",
        json_schema_extra={"example": "image"},
    )
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description="Bounding box of the image when parser coordinates are available.",
    )
    captions: List[CaptionNode] = Field(
        default_factory=list,
        description="Captions associated with this image.",
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list,
        description="Footnotes associated with this image.",
    )


class ArticleNode(BaseModel):
    """Article-level grouping of headline, body blocks, and related media."""

    article_id: str = Field(
        ...,
        description="Stable identifier for the article within the parsed document.",
        json_schema_extra={"example": "article-1"},
    )
    headline: str = Field(
        ...,
        description="Primary headline text for the article.",
        json_schema_extra={"example": "New Economic Policy Announced"},
    )
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description="Bounding box enclosing the article when parser coordinates are available.",
    )
    body_blocks: List[str] = Field(
        default_factory=list,
        description="Ordered text blocks that make up the article body.",
    )
    images: List[ImageNode] = Field(
        default_factory=list,
        description="Images associated with the article.",
    )
    captions: List[CaptionNode] = Field(
        default_factory=list,
        description="Captions associated with the article.",
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list,
        description="Footnotes associated with the article.",
    )


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int = Field(
        ...,
        description="One-based page number from the parsed PDF.",
        json_schema_extra={"example": 1},
    )
    width: Optional[float] = Field(
        default=None,
        description="Page width reported by the parser, if available.",
    )
    height: Optional[float] = Field(
        default=None,
        description="Page height reported by the parser, if available.",
    )
    articles: List[ArticleNode] = Field(
        default_factory=list,
        description="Articles extracted from this page.",
    )
    ads: List[str] = Field(
        default_factory=list,
        description="Advertisement text blocks extracted from this page.",
    )
    headers: List[str] = Field(
        default_factory=list,
        description="Header text blocks extracted from this page.",
    )
    footers: List[str] = Field(
        default_factory=list,
        description="Footer text blocks extracted from this page.",
    )
    page_numbers: List[str] = Field(
        default_factory=list,
        description="Visible page-number text blocks extracted from this page.",
    )


class ParseQuality(BaseModel):
    """Quality metadata describing parser provenance and warnings."""

    status: str = Field(
        default="success",
        description="Parsing operation status indicator.",
        json_schema_extra={"example": "success"},
    )
    parser: str = Field(
        default="mineru",
        description="The underlying engine used to parse the PDF.",
        json_schema_extra={"example": "mineru"},
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered during the parsing process.",
    )


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str = Field(
        ...,
        description="Unique identifier for the parsed document.",
        json_schema_extra={"example": "doc-5f8a9c"},
    )
    pages: List[PageNode] = Field(
        default_factory=list,
        description="Sequential list of structured pages extracted from the PDF.",
    )
    quality: ParseQuality = Field(
        default_factory=ParseQuality,
        description="Metadata detailing parsing provenance and encountered warnings.",
    )


class HealthResponse(BaseModel):
    """Liveness response model for deployment health checks."""

    status: str = Field(
        default="ok",
        description="Current operational status of the service.",
        json_schema_extra={"example": "ok"},
    )
