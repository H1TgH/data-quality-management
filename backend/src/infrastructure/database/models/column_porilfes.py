from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime as PGDateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.database import Base


class FieldProfileModel(Base):
    __tablename__ = "field_profiles"

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True
    )

    field_name: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    data_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    fill_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )

    distinct_count: Mapped[int | None] = mapped_column(
        Integer
    )

    min_value: Mapped[str | None] = mapped_column(
        String
    )

    max_value: Mapped[str | None] = mapped_column(
        String
    )

    profiled_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
