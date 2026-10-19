from uuid import uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.rules.enums import RuleTypeEnum
from infrastructure.database.database import Base


class CleanedRowsModel(Base):
    __tablename__ = "cleaned_rows"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False
    )

    rule_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("rules.id", ondelete="SET NULL")
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
