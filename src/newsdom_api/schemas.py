"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

BOUNDING_BOX_EXAMPLE = {"x0": 120.0, "y0": 320.0, "x1": 420.0, "y1": 560.0}
CAPTION_EXAMPLE = {
    "text": "Photo caption text extracted from the newspaper page.",
    "bbox": {"x0": 120.0, "y0": 565.0, "x1": 420.0, "y1": 620.0},
}
IMAGE_EXAMPLE = {
    "path": "extracted_images/page1_img1.jpg",
    "media_type": "image",
    "bbox": BOUNDING_BOX_EXAMPLE,
    "captions": [CAPTION_EXAMPLE],
    "footnotes": [],
}
ARTICLE_EXAMPLE = {
    "article_id": "page-1-article-1",
    "headline": "Morning edition headline",
    "bbox": {"x0": 10.0, "y0": 20.0, "x1": 760.0, "y1": 900.0},
    "body_blocks": [
        "First paragraph of the article body.",
        "Second paragraph continues the story.",
    ],
    "images": [IMAGE_EXAMPLE],
    "captions": [],
    "footnotes": [],
}
PAGE_EXAMPLE = {
    "page_number": 1,
    "width": 800.5,
    "height": 1200.0,
    "articles": [ARTICLE_EXAMPLE],
    "ads": ["Advertisement block text"],
    "headers": ["2026-04-09 morning edition"],
    "footers": ["Published by NewsDOM sample publisher"],
    "page_numbers": ["1"],
}
PARSE_QUALITY_EXAMPLE = {
    "status": "success",
    "parser": "mineru",
    "warnings": ["Page 1: overlapping layout blocks were normalized."],
}
PARSE_RESPONSE_EXAMPLE = {
    "document_id": "sample-newspaper",
    "pages": [PAGE_EXAMPLE],
    "quality": PARSE_QUALITY_EXAMPLE,
}
HEALTH_RESPONSE_EXAMPLE = {"status": "ok"}
ERROR_RESPONSE_EXAMPLE = {"detail": "Unsupported Media Type"}


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(..., description="Leftmost X coordinate of the bounding box.")
    y0: float = Field(..., description="Topmost Y coordinate of the bounding box.")
    x1: float = Field(..., description="Rightmost X coordinate of the bounding box.")
    y1: float = Field(..., description="Bottommost Y coordinate of the bounding box.")

    model_config = {"json_schema_extra": {"example": BOUNDING_BOX_EXAMPLE}}


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(..., description="Text content of the caption.")
    bbox: Optional[BoundingBox] = Field(
        default=None,
        description="Bounding box of the caption when parser coordinates are available.",
    )

    model_config = {"json_schema_extra": {"example": CAPTION_EXAMPLE}}


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(..., description="Relative path to the extracted image asset.")
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

    model_config = {"json_schema_extra": {"example": IMAGE_EXAMPLE}}


class ArticleNode(BaseModel):
    """Article-level grouping of headline, body blocks, and related media."""

    article_id: str = Field(
        ..., description="Stable identifier for the article within the parsed document."
    )
    headline: str = Field(..., description="Primary headline text for the article.")
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

    model_config = {"json_schema_extra": {"example": ARTICLE_EXAMPLE}}


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int = Field(
        ..., description="One-based page number from the parsed PDF."
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

    model_config = {"json_schema_extra": {"example": PAGE_EXAMPLE}}


class ParseQuality(BaseModel):
    """Quality metadata describing parser provenance and warnings."""

    status: str = Field(
        default="success", description="Parsing operation status indicator."
    )
    parser: str = Field(
        default="mineru", description="The underlying engine used to parse the PDF."
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings encountered during the parsing process.",
    )

    model_config = {"json_schema_extra": {"example": PARSE_QUALITY_EXAMPLE}}


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str = Field(
        ..., description="Unique identifier for the parsed document."
    )
    pages: List[PageNode] = Field(
        default_factory=list,
        description="Sequential list of structured pages extracted from the PDF.",
    )
    quality: ParseQuality = Field(
        default_factory=ParseQuality,
        description="Metadata detailing parsing provenance and encountered warnings.",
    )

    model_config = {"json_schema_extra": {"example": PARSE_RESPONSE_EXAMPLE}}


class HealthResponse(BaseModel):
    """Liveness response model for deployment health checks."""

    status: str = Field(
        default="ok",
        description="Current operational status of the service.",
    )

    model_config = {"json_schema_extra": {"example": HEALTH_RESPONSE_EXAMPLE}}


class ErrorResponse(BaseModel):
    """Standardized error response model for HTTP exceptions."""

    detail: str = Field(
        ...,
        description="A clear and specific error message describing what went wrong.",
    )

    model_config = {"json_schema_extra": {"example": ERROR_RESPONSE_EXAMPLE}}
