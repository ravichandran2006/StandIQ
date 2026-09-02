from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SourceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("source_type", "external_identifier", name="uq_source_records_type_identifier"),
        Index("ix_source_records_type_identifier", "source_type", "external_identifier"),
    )

    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    external_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    source_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingestion_run_id: Mapped[str | None] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="SET NULL"), index=True)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)

    ingestion_run = relationship("IngestionRun", back_populates="source_records")
    standards = relationship("Standard", back_populates="source_record")