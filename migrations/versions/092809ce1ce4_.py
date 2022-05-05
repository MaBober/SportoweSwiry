"""empty message

Revision ID: 092809ce1ce4
Revises: 
Create Date: 2022-05-05 21:04:51.825936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '092809ce1ce4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('readMessage', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'readMessage')
    # ### end Alembic commands ###
