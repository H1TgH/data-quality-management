from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime as PGDateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.core.runs.enums import RunStatusEnum, RunTriggerEnum
from backend.src.infrastructure.database.database import Base


class RunModel(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    trigger: Mapped[RunTriggerEnum] = mapped_column(
        ENUM(RunTriggerEnum, name="run_trigger"),
        nullable=False
    )

    status: Mapped[RunStatusEnum] = mapped_column(
        ENUM(RunStatusEnum, name="run_status"),
        nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        PGDateTime(timezone=True)
    )

    rows_total: Mapped[int | None] = mapped_column(
        Integer
    )

    rows_removed: Mapped[int | None] = mapped_column(
        Integer
    )

    errors_count: Mapped[int | None] = mapped_column(
        Integer
    )

    quality_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2)
    )
