"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(description="The x-coordinate of the top-left corner.")
    y0: float = Field(description="The y-coordinate of the top-left corner.")
    x1: float = Field(description="The x-coordinate of the bottom-right corner.")
    y1: float = Field(description="The y-coordinate of the bottom-right corner.")


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(description="The textual content of the caption.")
    bbox: Optional[BoundingBox] = Field(
        default=None, description="The bounding box of the caption on the page."
    )


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(
        description="The file path or identifier for the extracted image."
    )
    media_type: str = Field(default="image", description="The type of media.")
    bbox: Optional[BoundingBox] = Field(
        default=None, description="The bounding box of the image on the page."
    )
    captions: List[CaptionNode] = Field(
        default_factory=list, description="Captions associated with this image."
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list, description="Footnotes associated with this image."
    )


class ArticleNode(BaseModel):
    """Article-level grouping of headline, body blocks, and related media."""

    article_id: str = Field(description="Unique identifier for the article.")
    headline: str = Field(description="The headline or title of the article.")
    bbox: Optional[BoundingBox] = Field(
        default=None, description="The bounding box of the entire article area."
    )
    body_blocks: List[str] = Field(
        default_factory=list,
        description="List of text blocks constituting the article body.",
    )
    images: List[ImageNode] = Field(
        default_factory=list, description="Images belonging to this article."
    )
    captions: List[CaptionNode] = Field(
        default_factory=list,
        description="Captions extracted within the article context.",
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list,
        description="Footnotes extracted within the article context.",
    )


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int = Field(description="The 1-based page number.")
    width: Optional[float] = Field(
        default=None, description="The width of the page in coordinates."
    )
    height: Optional[float] = Field(
        default=None, description="The height of the page in coordinates."
    )
    articles: List[ArticleNode] = Field(
        default_factory=list, description="Articles extracted from this page."
    )
    ads: List[str] = Field(
        default_factory=list, description="Advertisement blocks found on this page."
    )
    headers: List[str] = Field(
        default_factory=list, description="Header text blocks found on this page."
    )
    footers: List[str] = Field(
        default_factory=list, description="Footer text blocks found on this page."
    )
    page_numbers: List[str] = Field(
        default_factory=list,
        description="Page number text blocks extracted from the page.",
    )


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


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str = Field(description="Unique identifier for the parsed document.")
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
    )
