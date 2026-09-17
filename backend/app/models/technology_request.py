from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TechnologyRequest(Base):
    """A technology a public visitor asked us to start tracking.

    Requests are queued for an admin to review and, if it makes sense, hand-
    configure in seed.py (trusted/official domains, query templates) the same
    way every other tracked Technology is. Approving here is just a status
    marker — it does not create a Technology row on its own, since bad domain
    guesses would silently ingest the wrong content.
    """

    __tablename__ = "technology_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
