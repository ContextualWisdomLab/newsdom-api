"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str
    bbox: Optional[BoundingBox] = None


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str
    media_type: str = "image"
    bbox: Optional[BoundingBox] = None
    captions: List[CaptionNode] = Field(default_factory=list)
    footnotes: List[CaptionNode] = Field(default_factory=list)


class ArticleNode(BaseModel):
    """Article-level grouping of headline, body blocks, and related media."""

    article_id: str
    headline: str
    bbox: Optional[BoundingBox] = None
    body_blocks: List[str] = Field(default_factory=list)
    images: List[ImageNode] = Field(default_factory=list)
    captions: List[CaptionNode] = Field(default_factory=list)
    footnotes: List[CaptionNode] = Field(default_factory=list)


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None
    articles: List[ArticleNode] = Field(default_factory=list)
    ads: List[str] = Field(default_factory=list)
    headers: List[str] = Field(default_factory=list)
    footers: List[str] = Field(default_factory=list)
    page_numbers: List[str] = Field(default_factory=list)


class ParseQuality(BaseModel):
    """Quality metadata describing parser provenance and warnings."""

    status: str = "success"
    parser: str = "mineru"
    warnings: List[str] = Field(default_factory=list)


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str
    pages: List[PageNode] = Field(default_factory=list)
    quality: ParseQuality = Field(default_factory=ParseQuality)
