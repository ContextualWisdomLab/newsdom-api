"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(
        description="Leftmost X coordinate of the bounding box.",
        json_schema_extra={"example": 10.5},
    )
    y0: float = Field(
        description="Topmost Y coordinate of the bounding box.",
        json_schema_extra={"example": 100.0},
    )
    x1: float = Field(
        description="Rightmost X coordinate of the bounding box.",
        json_schema_extra={"example": 500.5},
    )
    y1: float = Field(
        description="Bottommost Y coordinate of the bounding box.",
        json_schema_extra={"example": 800.0},
    )


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(
        description="Text content of the caption.",
        json_schema_extra={"example": "写真：昨日の大雨の様子"},
    )
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description=(
            "Bounding box of the caption when parser coordinates are available."
        ),
    )


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(
        description="Relative path to the extracted image asset.",
        json_schema_extra={"example": "images/article_123_fig1.jpg"},
    )
    media_type: str = Field(
        default="image",
        description="Media type label for the extracted image node.",
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
    """Section-level grouping of a heading, body blocks, and related media.

    Despite the ``article`` naming (retained for schema stability), this node is
    language- and domain-agnostic: it models any logically grouped region of a
    document, such as a report section, chapter, or column.
    """

    article_id: str = Field(
        description="Stable identifier for the section within the parsed document.",
        json_schema_extra={"example": "section-20231015-001"},
    )
    headline: str = Field(
        ...,
        description=(
            "Primary section heading text. This is a generic section heading, "
            "not tied to any newspaper or language-specific concept."
        ),
        json_schema_extra={"example": "Quarterly results"},
    )
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description=(
            "Bounding box enclosing the article when parser coordinates are available."
        ),
    )
    body_blocks: List[str] = Field(
        default_factory=list,
        description="Ordered text blocks that make up the article body.",
        json_schema_extra={"example": ["First paragraph of the article.", "Second paragraph."]},
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
        description="One-based page number from the parsed PDF.",
        json_schema_extra={"example": 1},
    )
    width: Optional[float] = Field(
        default=None,
        description="Page width reported by the parser, if available.",
        examples=[595.28],
    )
    height: Optional[float] = Field(
        default=None,
        description="Page height reported by the parser, if available.",
        examples=[841.89],
    )
    articles: List[ArticleNode] = Field(
        default_factory=list,
        description="Articles extracted from this page.",
    )
    ads: List[str] = Field(
        default_factory=list,
        description="Advertisement text blocks extracted from this page.",
        examples=[["Example advertisement text"]],
    )
    headers: List[str] = Field(
        default_factory=list,
        description="Header text blocks extracted from this page.",
        examples=[["Quarterly report", "2026 Q2"]],
    )
    footers: List[str] = Field(
        default_factory=list,
        description="Footer text blocks extracted from this page.",
        examples=[["Confidential"]],
    )
    page_numbers: List[str] = Field(
        default_factory=list,
        description="Visible page-number text blocks extracted from this page.",
        examples=[["1", "Page 1"]],
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
        json_schema_extra={"example": ["Image extraction failed on page 1."]},
    )


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str = Field(
        description="Unique identifier for the parsed document.",
        json_schema_extra={"example": "doc-a1b2c3d4"},
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


class ReadinessResponse(BaseModel):
    """Traffic-readiness response emitted only when all required dependencies work."""

    status: str = Field(
        default="ready",
        description="Stable traffic-readiness status.",
        json_schema_extra={"example": "ready"},
    )
