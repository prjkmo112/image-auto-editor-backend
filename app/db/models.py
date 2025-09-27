from typing import List, Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, BOOLEAN
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime

class Base(DeclarativeBase):
    pass


class ProcessedImages(Base):
    __tablename__ = 'processed_images'
    __table_args__ = (
        CheckConstraint("marked_file_mime_type::text ~* '^image/'::text", name='processed_images_marked_file_mime_type_check'),
        CheckConstraint("file_hash::text ~ '^[0-9a-f]{64}$'::text", name='processed_images_file_hash_check'),
        CheckConstraint("sliced_file_mime_type::text ~* '^image/'::text", name='processed_images_sliced_file_mime_type_check'),
        PrimaryKeyConstraint('id', name='processed_images_pkey'),
        UniqueConstraint('file_hash', name='processed_images_file_hash_key'),
        Index('processed_images_created_at_index', 'created_at')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    marked_file_path: Mapped[str] = mapped_column(String(500))
    marked_file_type: Mapped[str] = mapped_column(String(10), server_default=text("'local'::character varying"))
    marked_file_size: Mapped[Optional[int]] = mapped_column(Integer)
    marked_file_mime_type: Mapped[Optional[str]] = mapped_column(String(50))
    sliced_file_path: Mapped[str] = mapped_column(String(500))
    sliced_file_type: Mapped[str] = mapped_column(String(10), server_default=text("'local'::character varying"))
    sliced_file_size: Mapped[Optional[int]] = mapped_column(Integer)
    sliced_file_mime_type: Mapped[Optional[str]] = mapped_column(String(50))
    url_id: Mapped[Optional[str]] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))


class SourceImages(Base):
    __tablename__ = 'source_images'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='source_images_pkey'),
        Index('idx_source_images_created_at', 'created_at'),
        Index('idx_source_images_file_hash', 'file_hash'),
        Index('idx_source_images_status', 'status'),
        Index('idx_source_images_tags_gin', 'tags', postgresql_using='gin')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(BigInteger)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_hash: Mapped[str] = mapped_column(String(64))
    tags: Mapped[list[str]] = mapped_column(
        # MutableList.as_mutable(ARRAY(Text())),
        ARRAY(Text()),
        default=list,
        server_default=text('ARRAY[]::text[]'),
        nullable=False
    )
    file_path_type: Mapped[str] = mapped_column(String(50), server_default=text("'local'::character varying"))
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'uploaded'::character varying"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))

    processing_jobs: Mapped[List['ProcessingJobs']] = relationship('ProcessingJobs', back_populates='source_image')


class TargetImages(Base):
    __tablename__ = 'target_images'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='target_images_pkey'),
        UniqueConstraint('file_hash', name='target_images_file_hash_key'),
        Index('idx_target_images_active', 'is_active'),
        Index('idx_target_images_created_at', 'created_at'),
        Index('idx_target_images_tags_gin', 'tags', postgresql_using='gin')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(BigInteger)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_hash: Mapped[str] = mapped_column(String(64))
    tags: Mapped[list[str]] = mapped_column(
        # MutableList.as_mutable(ARRAY(Text())),
        ARRAY(Text()),
        default=list,
        server_default=text('ARRAY[]::text[]'),
        nullable=False
    )
    file_path_type: Mapped[str] = mapped_column(String(50), server_default=text("'local'::character varying"))
    is_active: Mapped[Optional[bool]] = mapped_column(BOOLEAN, server_default=text('true'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    url_id: Mapped[Optional[str]] = mapped_column(String(255))


class ProcessingJobs(Base):
    __tablename__ = 'processing_jobs'
    __table_args__ = (
        ForeignKeyConstraint(['source_image_id'], ['source_images.id'], ondelete='CASCADE', name='processing_jobs_source_image_id_fkey'),
        PrimaryKeyConstraint('id', name='processing_jobs_pkey'),
        Index('idx_processing_jobs_created_at', 'created_at'),
        Index('idx_processing_jobs_job_type', 'job_type'),
        Index('idx_processing_jobs_source_image', 'source_image_id'),
        Index('idx_processing_jobs_status', 'status'),
        Index('idx_processing_jobs_status_type', 'status', 'job_type')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_image_id: Mapped[int] = mapped_column(BigInteger)
    job_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'pending'::character varying"))
    request_params: Mapped[Optional[dict]] = mapped_column(JSONB)
    result_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    result_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    processing_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    result_file_path_type: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("'local'::character varying"))

    source_image: Mapped['SourceImages'] = relationship('SourceImages', back_populates='processing_jobs')
