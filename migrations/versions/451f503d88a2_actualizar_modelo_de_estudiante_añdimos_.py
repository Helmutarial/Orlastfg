"""Actualizar modelo de Estudiante: añdimos tabla foto y relaciones

Revision ID: 451f503d88a2
Revises: abf33e5979ec
Create Date: 2024-05-03 13:05:26.337030

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '451f503d88a2'
down_revision = 'abf33e5979ec'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('foto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estudiante_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_estudiante_id', 'estudiante', ['estudiante_id'], ['id'])


    # ### end Alembic commands ###

def downgrade():
    with op.batch_alter_table('foto', schema=None) as batch_op:
        batch_op.drop_constraint('fk_estudiante_id', type_='foreignkey')
        batch_op.drop_column('estudiante_id')
    # ### end Alembic commands ###
