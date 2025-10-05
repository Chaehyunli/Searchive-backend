# -*- coding: utf-8 -*-
"""문서-태그 연결 테이블 생성

Revision ID: c6f1eb7cc27f
Revises: 645628589f3a
Create Date: 2025-10-05 15:59:11.436660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic에서 사용하는 리비전 식별자
revision: str = 'c6f1eb7cc27f'
down_revision: Union[str, Sequence[str], None] = '645628589f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """스키마 업그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.create_table('document_tags',
    sa.Column('document_id', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.tag_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )
    # ### Alembic 명령어 끝 ###


def downgrade() -> None:
    """스키마 다운그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.drop_table('document_tags')
    # ### Alembic 명령어 끝 ###
