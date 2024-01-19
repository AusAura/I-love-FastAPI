"""add_is_revoker_to_user

Revision ID: 18074765ce10
Revises: 595b82031331
Create Date: 2024-01-19 20:08:13.196845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18074765ce10'
down_revision: Union[str, None] = '595b82031331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_revoked', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_revoked')
    # ### end Alembic commands ###