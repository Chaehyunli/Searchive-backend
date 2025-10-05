# -*- coding: utf-8 -*-
"""태그 테이블 생성

Revision ID: 4e704fe4fa10
Revises: d676dbe50c6b
Create Date: 2025-10-05 15:58:13.386482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic에서 사용하는 리비전 식별자
revision: str = '4e704fe4fa10'
down_revision: Union[str, Sequence[str], None] = 'd676dbe50c6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """스키마 업그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.create_table('tags',
    sa.Column('tag_id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('tag_id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    # ### Alembic 명령어 끝 ###


def downgrade() -> None:
    """스키마 다운그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')
    # ### Alembic 명령어 끝 ###
