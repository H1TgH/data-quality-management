from uuid import uuid4

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.error_logs.enums import ErrorStatusEnum
from core.rules.enums import RuleTypeEnum
from infrastructure.database.database import Base


class ErrorLogModel(Base):
    __tablename__ = "error_log"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    run_id: Mapped[int] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False
    )

    rule_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("rules.id", ondelete="SET NULL")
    )

    rule_type: Mapped[RuleTypeEnum] = mapped_column(
        ENUM(RuleTypeEnum, name="rule_type"),
        nullable=False
    )

    target_columns: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False
    )

    row_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    status: Mapped[ErrorStatusEnum] = mapped_column(
        ENUM(ErrorStatusEnum, name="error_status"),
        nullable=False,
        server_default=text("'OPEN'")
    )
