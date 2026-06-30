"""
Modelos do banco de dados SQLAlchemy.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey, Float, create_engine
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Type alias for JSON columns (avoid Mapped generic issues)
JSONList = list
JSONDict = dict

from config import settings


class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ─── Formulario ─────────────────────────────────────────────

class Form(Base):
    __tablename__ = "forms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Schema dos campos (JSON)
    #   [ { "id": "uuid", "type": "text", "label": "...", "required": true,
    #       "placeholder": "", "help_text": "", "options": [], "validation": {},
    #       "edocs_mapping": null, "sort_order": 0 }, ... ]
    fields_schema = Column(JSON, default=list, nullable=False)

    # Configuracao de integracao com E-Docs
    #   { "auto_submit": true,
    #     "document": { "valor_legal": "Original", "natureza": "NatoDigital",
    #                   "classe_documental_id": null, "restricao_acesso": {} },
    #     "process": { "autuar": false, "classe_documental_id": null,
    #                  "assunto_template": "Formulario: {{ form_name }}"} }
    edocs_config = Column(JSON, nullable=True, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    submissions = relationship("Submission", back_populates="form", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Form {self.slug}>"


# ─── Submissao ──────────────────────────────────────────────

class SubmissionStatus:
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    PDF_GENERATED = "pdf_generated"
    SENT_TO_EDOCS = "sent_to_edocs"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    form_id: Mapped[str] = mapped_column(String(36), ForeignKey("forms.id"), nullable=False, index=True)

    # Dados preenchidos (JSON)
    data = Column(JSON, default=dict, nullable=False)

    # Metadados
    submitter_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    submitter_email: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    submitter_cpf: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default=SubmissionStatus.DRAFT, index=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)

    # PDF gerado
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Integracao E-Docs
    edocs_id_arquivo: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    edocs_id_documento: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    edocs_id_processo: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    edocs_id_encaminhamento: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    edocs_id_evento: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    edocs_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edocs_log = Column(JSON, default=list)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    form = relationship("Form", back_populates="submissions")

    def __repr__(self):
        return f"<Submission {self.protocol or self.id}>"


# ─── Log de Auditoria ───────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    submission_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ─── Engine ─────────────────────────────────────────────────

engine = None


def get_engine():
    global engine
    if engine is None:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
            echo=settings.log_level == "DEBUG",
        )
    return engine


def init_db():
    eng = get_engine()
    Base.metadata.create_all(eng)
    return eng


def get_session():
    from sqlalchemy.orm import sessionmaker
    eng = get_engine()
    Session = sessionmaker(bind=eng)
    return Session()
