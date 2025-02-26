"""Update mailbox table columns

Revision ID: 782b32156006
Revises: af8e5dbf47a6
Create Date: 2022-12-18 13:50:50.611047

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '782b32156006'
down_revision = 'af8e5dbf47a6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mailbox_message', sa.Column('sender_name', sa.String(length=50), nullable=True))
    op.add_column('mailbox_message', sa.Column('receiver_name', sa.String(length=50), nullable=True))
    op.add_column('mailbox_message', sa.Column('send_by_app', sa.Boolean(), nullable=False))
    op.add_column('mailbox_message', sa.Column('send_by_email', sa.Boolean(), nullable=False))
    op.add_column('mailbox_message', sa.Column('message_readed', sa.Boolean(), nullable=False))
    op.add_column('mailbox_message', sa.Column('multiple_message', sa.Boolean(), nullable=False))
    op.drop_column('mailbox_message', 'sendByApp')
    op.drop_column('mailbox_message', 'senderName')
    op.drop_column('mailbox_message', 'receiverName')
    op.drop_column('mailbox_message', 'multipleMessage')
    op.drop_column('mailbox_message', 'messageReaded')
    op.drop_column('mailbox_message', 'sendByEmail')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mailbox_message', sa.Column('sendByEmail', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.add_column('mailbox_message', sa.Column('messageReaded', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.add_column('mailbox_message', sa.Column('multipleMessage', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.add_column('mailbox_message', sa.Column('receiverName', mysql.VARCHAR(length=50), nullable=True))
    op.add_column('mailbox_message', sa.Column('senderName', mysql.VARCHAR(length=50), nullable=True))
    op.add_column('mailbox_message', sa.Column('sendByApp', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.drop_column('mailbox_message', 'multiple_message')
    op.drop_column('mailbox_message', 'message_readed')
    op.drop_column('mailbox_message', 'send_by_email')
    op.drop_column('mailbox_message', 'send_by_app')
    op.drop_column('mailbox_message', 'receiver_name')
    op.drop_column('mailbox_message', 'sender_name')
    # ### end Alembic commands ###
