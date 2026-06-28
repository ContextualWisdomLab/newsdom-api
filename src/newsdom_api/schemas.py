"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(..., description="The left coordinate of the bounding box.")
    y0: float = Field(..., description="The top coordinate of the bounding box.")
    x1: float = Field(..., description="The right coordinate of the bounding box.")
    y1: float = Field(..., description="The bottom coordinate of the bounding box.")


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(..., description="The textual content of the caption.")
    bbox: Optional[BoundingBox] = Field(
        None, description="The bounding box of the caption."
    )


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(..., description="The path or identifier of the image file.")
    media_type: str = Field("image", description="The media type of the resource.")
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

    article_id: str = Field(..., description="The unique identifier for the article.")
    headline: str = Field(..., description="The headline or title of the article.")
    bbox: Optional[BoundingBox] = Field(
        None, description="The bounding box of the entire article."
    )
    body_blocks: List[str] = Field(
        default_factory=list,
        description="The text blocks composing the body of the article.",
    )
    images: List[ImageNode] = Field(
        default_factory=list, description="Images belonging to the article."
    )
    captions: List[CaptionNode] = Field(
        default_factory=list, description="Captions associated with the article."
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list, description="Footnotes associated with the article."
    )


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int = Field(..., description="The 1-based page number.")
    width: Optional[float] = Field(None, description="The width of the page in points.")
    height: Optional[float] = Field(
        None, description="The height of the page in points."
    )
    articles: List[ArticleNode] = Field(
        default_factory=list, description="Articles detected on the page."
    )
    ads: List[str] = Field(
        default_factory=list, description="Advertisements detected on the page."
    )
    headers: List[str] = Field(
        default_factory=list, description="Header elements on the page."
    )
    footers: List[str] = Field(
        default_factory=list, description="Footer elements on the page."
    )
    page_numbers: List[str] = Field(
        default_factory=list, description="Page number texts extracted from the page."
    )


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
