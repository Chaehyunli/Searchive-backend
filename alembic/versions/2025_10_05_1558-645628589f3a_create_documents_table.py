# -*- coding: utf-8 -*-
"""문서 테이블 생성

Revision ID: 645628589f3a
Revises: 4e704fe4fa10
Create Date: 2025-10-05 15:58:41.438777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic에서 사용하는 리비전 식별자
revision: str = '645628589f3a'
down_revision: Union[str, Sequence[str], None] = '4e704fe4fa10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """스키마 업그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.create_table('documents',
    sa.Column('document_id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('storage_path', sa.String(length=1024), nullable=False),
    sa.Column('file_type', sa.String(length=100), nullable=False),
    sa.Column('file_size_kb', sa.Integer(), nullable=True),
    sa.Column('uploaded_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('document_id'),
    sa.UniqueConstraint('storage_path')
    )
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    # ### Alembic 명령어 끝 ###


def downgrade() -> None:
    """스키마 다운그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_table('documents')
    # ### Alembic 명령어 끝 ###
