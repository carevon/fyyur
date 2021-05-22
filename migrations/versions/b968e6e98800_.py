"""empty message

Revision ID: b968e6e98800
Revises: 0349cfd0abf5
Create Date: 2021-05-16 02:49:44.131847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b968e6e98800'
down_revision = '0349cfd0abf5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_description', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'seeking_description')
    # ### end Alembic commands ###