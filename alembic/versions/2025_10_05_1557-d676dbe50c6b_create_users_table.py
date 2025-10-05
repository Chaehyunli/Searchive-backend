# -*- coding: utf-8 -*-
"""사용자 테이블 생성

Revision ID: d676dbe50c6b
Revises:
Create Date: 2025-10-05 15:57:46.471025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic에서 사용하는 리비전 식별자
revision: str = 'd676dbe50c6b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """스키마 업그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.create_table('users',
    sa.Column('user_id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('kakao_id', sa.String(length=255), nullable=False),
    sa.Column('nickname', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_kakao_id'), 'users', ['kakao_id'], unique=True)
    # ### Alembic 명령어 끝 ###


def downgrade() -> None:
    """스키마 다운그레이드"""
    # ### Alembic에서 자동 생성한 명령어 - 필요시 수정 ###
    op.drop_index(op.f('ix_users_kakao_id'), table_name='users')
    op.drop_table('users')
    # ### Alembic 명령어 끝 ###
