from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Author(BaseModel):
    name: str
    orcid: Optional[str] = None


class PaperUrls(BaseModel):
    doi: Optional[str] = None
    source: Optional[str] = None
    open_access_pdf: Optional[str] = None


class PaperBase(BaseModel):
    doi: Optional[str] = None
    title: str
    authors: List[Author] = Field(default_factory=list)
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    publication_type: Optional[str] = None
    urls: PaperUrls = Field(default_factory=PaperUrls)
    citation_count: int = 0
    source_apis: List[str] = Field(default_factory=list)
    is_open_access: bool = False
    open_access_pdf: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class PaperCreate(PaperBase):
    pass


class PaperUpdate(BaseModel):
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class PaperOut(PaperBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaperSearchHit(PaperBase):
    """Ephemeral search hit with stable synthetic id when not persisted."""

    id: UUID


class TopicBase(BaseModel):
    name: str
    query: str
    sources: List[str] = Field(default_factory=lambda: ["crossref", "openalex"])
    filters: Dict[str, Any] = Field(default_factory=dict)


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    sources: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


class TopicOut(TopicBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_results_count: int = 0

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str
    sources: List[str] = Field(default_factory=lambda: ["crossref", "openalex"])
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class QueryTranslationInfo(BaseModel):
    free_text: str = ""
    from_year: Optional[int] = None
    until_year: Optional[int] = None
    parse_ok: bool = True
    parse_error: Optional[str] = None


class SearchResult(BaseModel):
    papers: List[PaperSearchHit]
    total: int
    sources: Dict[str, Any]
    query_translation: Optional[QueryTranslationInfo] = None


class ExportRequest(BaseModel):
    paper_ids: List[UUID] = Field(min_length=1)
    format: Literal["bibtex", "ris", "plain"] = "bibtex"


class ExportResponse(BaseModel):
    content: str
    format: str
