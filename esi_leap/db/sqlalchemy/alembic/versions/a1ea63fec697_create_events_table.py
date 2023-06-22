#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""create events table

Revision ID: a1ea63fec697
Revises:
Create Date: 2023-06-26 14:22:34.822066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1ea63fec697'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=255), nullable=False),
        sa.Column('event_time', sa.DateTime(), nullable=False),
        sa.Column('object_type', sa.String(length=255), nullable=True),
        sa.Column('object_uuid', sa.String(length=36), nullable=True),
        sa.Column('resource_type', sa.String(length=255), nullable=True),
        sa.Column('resource_uuid', sa.String(length=36), nullable=True),
        sa.Column('lessee_id', sa.String(length=36), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('event_type_idx', 'events', ['event_type'],
                    unique=False)
    op.create_index('event_lessee_id_idx', 'events', ['lessee_id'],
                    unique=False)
    op.create_index('event_owner_id_idx', 'events', ['owner_id'],
                    unique=False)
    op.create_index('event_resource_idx', 'events',
                    ['resource_type', 'resource_uuid'],
                    unique=False)


def downgrade():
    pass
