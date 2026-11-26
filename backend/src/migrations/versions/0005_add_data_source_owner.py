from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("data_sources", sa.Column("user_id", sa.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key(
        "fk_data_sources_user_id_users",
        "data_sources",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_data_sources_user_id_users", "data_sources", type_="foreignkey")
    op.drop_column("data_sources", "user_id")
