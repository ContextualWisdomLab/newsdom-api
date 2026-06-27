"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(
        ...,
        ge=0.0,
        le=1000000.0,
        description="The x-coordinate of the top-left corner.",
    )
    y0: float = Field(
        ...,
        ge=0.0,
        le=1000000.0,
        description="The y-coordinate of the top-left corner.",
    )
    x1: float = Field(
        ...,
        ge=0.0,
        le=1000000.0,
        description="The x-coordinate of the bottom-right corner.",
    )
    y1: float = Field(
        ...,
        ge=0.0,
        le=1000000.0,
        description="The y-coordinate of the bottom-right corner.",
    )


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(..., max_length=50000)
    bbox: Optional[BoundingBox] = None


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(..., max_length=512)
    media_type: str = Field("image", max_length=128)
    bbox: Optional[BoundingBox] = None
    captions: List[CaptionNode] = Field(default_factory=list, max_length=100)
    footnotes: List[CaptionNode] = Field(default_factory=list, max_length=100)


class ArticleNode(BaseModel):
    """Article-level grouping of headline, body blocks, and related media."""

    article_id: str = Field(..., max_length=128)
    headline: str = Field(..., max_length=50000)
    bbox: Optional[BoundingBox] = None
    body_blocks: List[str] = Field(default_factory=list, max_length=5000)
    images: List[ImageNode] = Field(default_factory=list, max_length=100)
    captions: List[CaptionNode] = Field(default_factory=list, max_length=100)
    footnotes: List[CaptionNode] = Field(default_factory=list, max_length=100)


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int = Field(..., ge=1, le=100000)
    width: Optional[float] = Field(None, ge=0.0, le=1000000.0)
    height: Optional[float] = Field(None, ge=0.0, le=1000000.0)
    articles: List[ArticleNode] = Field(default_factory=list, max_length=1000)
    ads: List[str] = Field(default_factory=list, max_length=1000)
    headers: List[str] = Field(default_factory=list, max_length=1000)
    footers: List[str] = Field(default_factory=list, max_length=1000)
    page_numbers: List[str] = Field(default_factory=list, max_length=1000)


class ParseQuality(BaseModel):
    """Quality metadata describing parser provenance and warnings."""

    status: str = Field("success", max_length=128)
    parser: str = Field("mineru", max_length=128)
    warnings: List[str] = Field(default_factory=list, max_length=100)


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str = Field(..., max_length=512)
    pages: List[PageNode] = Field(default_factory=list, max_length=10000)
    quality: ParseQuality = Field(default_factory=ParseQuality)
