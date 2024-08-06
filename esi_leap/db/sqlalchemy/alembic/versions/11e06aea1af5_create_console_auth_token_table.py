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

"""Create console auth token table

Revision ID: 11e06aea1af5
Revises: a1ea63fec697
Create Date: 2024-08-08 14:05:15.443900

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "11e06aea1af5"
down_revision = "a1ea63fec697"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "console_auth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("node_uuid", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "console_auth_tokens_node_uuid_idx",
        "console_auth_tokens",
        ["node_uuid"],
        unique=False,
    )


def downgrade():
    pass
