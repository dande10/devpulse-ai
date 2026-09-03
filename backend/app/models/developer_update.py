from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UpdateTechnology(Base):
    __tablename__ = "update_technologies"

    update_id: Mapped[int] = mapped_column(ForeignKey("developer_updates.id", ondelete="CASCADE"), primary_key=True)
    technology_id: Mapped[int] = mapped_column(ForeignKey("technologies.id", ondelete="CASCADE"), primary_key=True, index=True)


class DeveloperUpdate(Base):
    __tablename__ = "developer_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(700), nullable=False, unique=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    original_excerpt: Mapped[str | None] = mapped_column(Text)
    extracted_content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_matters: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    impact_level: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    content_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    source = relationship("Source", back_populates="updates")
    technologies = relationship("Technology", secondary="update_technologies", back_populates="updates")
