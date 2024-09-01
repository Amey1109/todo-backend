"""Create phone_number for user table

Revision ID: 4ccf8ff06ea4
Revises: 
Create Date: 2024-09-01 20:14:03.260900

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ccf8ff06ea4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String, nullable = True ))


def downgrade() -> None:
    pass
