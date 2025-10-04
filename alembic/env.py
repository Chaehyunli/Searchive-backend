import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- 🔽 [수정/추가 1] 프로젝트 경로 및 설정 import ---
# 프로젝트의 src 폴더를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import settings  # config.py에서 settings 객체 가져오기
from src.db.session import Base # SQLAlchemy Base 모델 가져오기

# 도메인 모델들을 import (alembic이 자동으로 테이블을 감지하도록)
from src.domains.users.models import User
# TODO: 다른 도메인 모델 추가 시 아래에 import 추가
# from src.domains.documents.models import Document
# ----------------------------------------------------

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- 🔽 [수정 2] SQLAlchemy URL 설정 ---
# alembic.ini의 sqlalchemy.url 대신, config.py에서 생성한 DATABASE_URL 사용
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
# ----------------------------------------------------


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# --- 🔽 [수정 3] target_metadata 설정 ---
target_metadata = Base.metadata
# ----------------------------------------------------

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
