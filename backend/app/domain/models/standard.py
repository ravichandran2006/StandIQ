from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Classification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "classifications"
    __table_args__ = (UniqueConstraint("scheme", "code", name="uq_classifications_scheme_code"),)

    scheme: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    standards = relationship("StandardClassification", back_populates="classification")


class StandardClassification(Base):
    __tablename__ = "standard_classifications"
    __table_args__ = (UniqueConstraint("standard_id", "classification_id", name="uq_standard_classifications_pair"),)

    standard_id: Mapped[str] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), primary_key=True)
    classification_id: Mapped[str] = mapped_column(ForeignKey("classifications.id", ondelete="CASCADE"), primary_key=True)

    standard = relationship("Standard", back_populates="classifications")
    classification = relationship("Classification", back_populates="standards")


class Standard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "standards"
    __table_args__ = (Index("ix_standards_title", "title"),)

    is_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    standard_type: Mapped[str | None] = mapped_column(String(80))
    publication_info: Mapped[str | None] = mapped_column(Text)
    review_info: Mapped[str | None] = mapped_column(Text)
    technical_committee: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    superseding_standard_id: Mapped[str | None] = mapped_column(ForeignKey("standards.id", ondelete="SET NULL"))
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    source_record = relationship("SourceRecord", back_populates="standards")
    superseding_standard = relationship("Standard", remote_side="Standard.id")
    versions = relationship("StandardVersion", back_populates="standard", cascade="all, delete-orphan")
    classifications = relationship("StandardClassification", back_populates="standard", cascade="all, delete-orphan")
    relationships_from = relationship("StandardRelationship", foreign_keys="StandardRelationship.source_standard_id", back_populates="source_standard", cascade="all, delete-orphan")
    relationships_to = relationship("StandardRelationship", foreign_keys="StandardRelationship.target_standard_id", back_populates="target_standard", cascade="all, delete-orphan")


class StandardVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "standard_versions"
    __table_args__ = (UniqueConstraint("standard_id", "edition_year", name="uq_standard_versions_standard_year"), Index("ix_standard_versions_year", "edition_year"))

    standard_id: Mapped[str] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    edition_label: Mapped[str] = mapped_column(String(100), nullable=False)
    edition_year: Mapped[int | None] = mapped_column(Integer)
    publication_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool | None] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    standard = relationship("Standard", back_populates="versions")
    amendments = relationship("Amendment", back_populates="standard_version", cascade="all, delete-orphan")
    source_record = relationship("SourceRecord")


class Amendment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "amendments"
    __table_args__ = (UniqueConstraint("standard_version_id", "amendment_label", name="uq_amendments_version_label"),)

    standard_version_id: Mapped[str] = mapped_column(ForeignKey("standard_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    amendment_label: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    publication_date: Mapped[date | None] = mapped_column(Date)
    details: Mapped[str | None] = mapped_column(Text)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    standard_version = relationship("StandardVersion", back_populates="amendments")
    source_record = relationship("SourceRecord")


class StandardRelationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "standard_relationships"
    __table_args__ = (
        UniqueConstraint("source_standard_id", "target_standard_id", "relationship_type", name="uq_standard_relationships_pair_type"),
        CheckConstraint("source_standard_id <> target_standard_id", name="no_self_reference"),
        Index("ix_standard_relationships_target_type", "target_standard_id", "relationship_type"),
    )

    source_standard_id: Mapped[str] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    target_standard_id: Mapped[str] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)
    evidence_note: Mapped[str | None] = mapped_column(Text)

    source_standard = relationship("Standard", foreign_keys=[source_standard_id], back_populates="relationships_from")
    target_standard = relationship("Standard", foreign_keys=[target_standard_id], back_populates="relationships_to")
    source_record = relationship("SourceRecord")
