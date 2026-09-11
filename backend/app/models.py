import re
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

topic_paper_association = Table(
    "topic_papers",
    Base.metadata,
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topics.id"), primary_key=True),
    Column("paper_id", UUID(as_uuid=True), ForeignKey("papers.id"), primary_key=True),
)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    filters = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_results_count = Column(Integer, default=0)

    papers = relationship("Paper", secondary=topic_paper_association, back_populates="topics")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doi = Column(String(255), nullable=True, index=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON, default=list)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    venue = Column(String(500), nullable=True)
    publication_type = Column(String(100), nullable=True)
    urls = Column(JSON, default=dict)
    citation_count = Column(Integer, default=0)
    source_apis = Column(JSON, default=list)
    is_open_access = Column(Boolean, default=False)
    open_access_pdf = Column(String(1000), nullable=True)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    topics = relationship("Topic", secondary=topic_paper_association, back_populates="papers")

    def to_normalized_title(self) -> str:
        title = (self.title or "").lower()
        title = re.sub(r"[^\w\s]", "", title, flags=re.UNICODE)
        title = re.sub(r"\s+", " ", title).strip()
        stop_words = {"the", "a", "an", "in", "on", "of", "and", "or", "for", "with"}
        words = [w for w in title.split() if w not in stop_words]
        return " ".join(words)

    @property
    def first_author(self) -> Optional[str]:
        if self.authors and len(self.authors) > 0:
            name = self.authors[0].get("name", "") if isinstance(self.authors[0], dict) else str(self.authors[0])
            return surname_lower(name)
        return None


def surname_lower(name: str) -> str:
    parts = (name or "").strip().split()
    return parts[-1].lower() if parts else ""
