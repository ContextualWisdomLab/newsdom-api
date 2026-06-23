"""Canonical response schemas for NewsDOM parsing results."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Axis-aligned bounding box expressed in page coordinates."""

    x0: float = Field(..., description="Left coordinate of the bounding box.")
    y0: float = Field(..., description="Top coordinate of the bounding box.")
    x1: float = Field(..., description="Right coordinate of the bounding box.")
    y1: float = Field(..., description="Bottom coordinate of the bounding box.")


class CaptionNode(BaseModel):
    """Caption text associated with an image or figure."""

    text: str = Field(..., description="Text content of the caption.")
    bbox: Optional[BoundingBox] = Field(
        None, description="Bounding box of the caption in page coordinates."
    )


class ImageNode(BaseModel):
    """Image metadata preserved in the canonical page structure."""

    path: str = Field(..., description="Path or URL to the extracted image file.")
    media_type: str = Field(
        "image", description="Type of the media, defaults to 'image'."
    )
    bbox: Optional[BoundingBox] = Field(
        None, description="Bounding box of the image in page coordinates."
    )
    captions: List[CaptionNode] = Field(
        default_factory=list, description="List of captions associated with the image."
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list, description="List of footnotes associated with the image."
    )


class ArticleNode(BaseModel):
    """Article-level grouping of headline, body blocks, and related media."""

    article_id: str = Field(..., description="Unique identifier for the article.")
    headline: str = Field(..., description="Headline text of the article.")
    bbox: Optional[BoundingBox] = Field(
        None, description="Bounding box encompassing the entire article."
    )
    body_blocks: List[str] = Field(
        default_factory=list,
        description="List of text blocks forming the body of the article.",
    )
    images: List[ImageNode] = Field(
        default_factory=list, description="List of images embedded within the article."
    )
    captions: List[CaptionNode] = Field(
        default_factory=list, description="List of captions related to the article."
    )
    footnotes: List[CaptionNode] = Field(
        default_factory=list, description="List of footnotes for the article."
    )


class PageNode(BaseModel):
    """Single parsed page including article, ad, and header groupings."""

    page_number: int = Field(
        ..., description="The sequential page number (1-based index)."
    )
    width: Optional[float] = Field(None, description="Width of the page.")
    height: Optional[float] = Field(None, description="Height of the page.")
    articles: List[ArticleNode] = Field(
        default_factory=list, description="Articles found on this page."
    )
    ads: List[str] = Field(
        default_factory=list, description="Advertisement texts detected on this page."
    )
    headers: List[str] = Field(
        default_factory=list, description="Header texts found on the page."
    )
    footers: List[str] = Field(
        default_factory=list, description="Footer texts found on the page."
    )
    page_numbers: List[str] = Field(
        default_factory=list, description="Page number labels detected on the page."
    )


class ParseQuality(BaseModel):
    """Quality metadata describing parser provenance and warnings."""

    status: str = Field(
        "success", description="Overall parsing status (e.g., 'success', 'failure')."
    )
    parser: str = Field("mineru", description="Name of the parser backend used.")
    warnings: List[str] = Field(
        default_factory=list, description="List of warnings generated during parsing."
    )


class ParseResponse(BaseModel):
    """Top-level API response for a parsed document."""

    document_id: str = Field(
        ..., description="Unique identifier for the parsed document."
    )
    pages: List[PageNode] = Field(
        default_factory=list,
        description="List of pages contained in the parsed document.",
    )
    quality: ParseQuality = Field(
        default_factory=ParseQuality,
        description="Quality metadata describing parser provenance and warnings.",
    )
