from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Certification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "certifications"
    __table_args__ = (UniqueConstraint("scheme_name", "external_identifier", name="uq_certifications_scheme_external"),)

    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    applicability_note: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    source_record = relationship("SourceRecord")


class QcoRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qco_records"
    __table_args__ = (UniqueConstraint("notification_number", name="uq_qco_records_notification"),)

    notification_number: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    source_record = relationship("SourceRecord")
    mappings = relationship("QcoMapping", back_populates="qco_record", cascade="all, delete-orphan")


class QcoMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qco_mappings"
    __table_args__ = (UniqueConstraint("qco_record_id", "standard_id", name="uq_qco_mappings_record_standard"),)

    qco_record_id: Mapped[str] = mapped_column(ForeignKey("qco_records.id", ondelete="CASCADE"), nullable=False, index=True)
    standard_id: Mapped[str] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    applicability_note: Mapped[str | None] = mapped_column(Text)

    qco_record = relationship("QcoRecord", back_populates="mappings")
    standard = relationship("Standard")


class CrsRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crs_records"
    __table_args__ = (UniqueConstraint("registration_number", name="uq_crs_records_registration"),)

    registration_number: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    source_record = relationship("SourceRecord")
    mappings = relationship("CrsMapping", back_populates="crs_record", cascade="all, delete-orphan")


class CrsMapping(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crs_mappings"
    __table_args__ = (UniqueConstraint("crs_record_id", "standard_id", name="uq_crs_mappings_record_standard"),)

    crs_record_id: Mapped[str] = mapped_column(ForeignKey("crs_records.id", ondelete="CASCADE"), nullable=False, index=True)
    standard_id: Mapped[str] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    applicability_note: Mapped[str | None] = mapped_column(Text)

    crs_record = relationship("CrsRecord", back_populates="mappings")
    standard = relationship("Standard")


class HallmarkingRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hallmarking_rules"
    __table_args__ = (Index("ix_hallmarking_rules_material", "material"),)

    rule_identifier: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    material: Mapped[str | None] = mapped_column(String(255))
    applicability_note: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_record_id: Mapped[str | None] = mapped_column(ForeignKey("source_records.id", ondelete="SET NULL"), index=True)

    source_record = relationship("SourceRecord")