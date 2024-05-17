"""Added first_name and last_name to User model

Revision ID: 2c42fe9f911c
Revises: 5235471990db
Create Date: 2024-05-17 14:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2c42fe9f911c'
down_revision = '5235471990db'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=64), nullable=True))

    # Setting default values for the new columns
    op.execute("UPDATE user SET first_name = 'Unknown' WHERE first_name IS NULL")
    op.execute("UPDATE user SET last_name = 'Unknown' WHERE last_name IS NULL")

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('first_name', existing_type=sa.String(length=64), nullable=False)
        batch_op.alter_column('last_name', existing_type=sa.String(length=64), nullable=False)

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('first_name')
        batch_op.drop_column('last_name')
