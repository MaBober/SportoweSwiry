"""empty message

Revision ID: 29608eb5be8e
Revises: 06d7318d1f94
Create Date: 2022-06-21 17:51:39.933014

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '29608eb5be8e'
down_revision = '06d7318d1f94'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activities', sa.Column('stravaID', sa.BigInteger(), nullable=True))
    op.drop_column('activities', 'week')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activities', sa.Column('week', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_column('activities', 'stravaID')
    # ### end Alembic commands ###