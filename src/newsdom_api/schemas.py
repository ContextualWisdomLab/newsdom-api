"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(..., description="The x-coordinate of the top-left corner.")
    y0: float = Field(..., description="The y-coordinate of the top-left corner.")
    x1: float = Field(..., description="The x-coordinate of the bottom-right corner.")
    y1: float = Field(..., description="The y-coordinate of the bottom-right corner.")


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(..., description="The text content of the caption.")
    bbox: Optional[BoundingBox] = Field(
        None, description="The bounding box of the caption."
    )


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(..., description="The path or identifier to the image.")
    media_type: str = Field("image", description="The media type of the node.")
    bbox: Optional[BoundingBox] = Field(
        None, description="The bounding box of the image."
    )
    captions: List[CaptionNode] = Field(
        default_factory=list, description="Captions associated with the image."
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list, description="Footnotes associated with the image."
    )


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
