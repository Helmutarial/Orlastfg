"""creando tabla reserva2

Revision ID: 4dcbe3b46ce3
Revises: 08be49eb7a3a
Create Date: 2024-03-30 20:48:03.834506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4dcbe3b46ce3'
down_revision = '08be49eb7a3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_estudiante')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('_alembic_tmp_estudiante',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=100), nullable=False),
    sa.Column('password', sa.VARCHAR(length=100), nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=100), nullable=True),
    sa.Column('apellidos', sa.VARCHAR(length=100), nullable=True),
    sa.Column('grado', sa.VARCHAR(length=100), nullable=True),
    sa.Column('especialidad', sa.VARCHAR(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    # ### end Alembic commands ###
