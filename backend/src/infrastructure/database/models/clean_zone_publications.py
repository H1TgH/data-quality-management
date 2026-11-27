from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime as PGDateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.database import Base


class CleanZonePublicationModel(Base):
    __tablename__ = "clean_zone_publications"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    view_schema: Mapped[str] = mapped_column(String, nullable=False)
    view_name: Mapped[str] = mapped_column(String, nullable=False)
    view_sql: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True), nullable=False, server_default=func.now()
    )
