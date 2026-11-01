from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime as PGDateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.infrastructure.database.database import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    data_source_id: Mapped[str] = mapped_column(
        UUID,
        ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False
    )

    schema_name: Mapped[str | None] = mapped_column(
        String
    )

    table_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
