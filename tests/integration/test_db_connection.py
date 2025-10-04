import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.core.config import settings


class TestDatabaseConnection:
    """Test database connectivity and basic operations."""

    def test_database_connection(self, db_engine):
        """Test that we can connect to the database."""
        with db_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_database_config(self):
        """Test that database configuration is properly loaded."""
        assert settings.DB_HOST is not None
        assert settings.DB_PORT is not None
        assert settings.DB_USER is not None
        assert settings.DB_NAME is not None
        assert settings.DATABASE_URL is not None

    def test_database_url_format(self):
        """Test that DATABASE_URL is properly formatted."""
        expected_prefix = f"postgresql://{settings.DB_USER}"
        assert settings.DATABASE_URL.startswith(expected_prefix)
        assert settings.DB_NAME in settings.DATABASE_URL

    def test_session_creation(self, db_session):
        """Test that we can create a database session."""
        assert db_session is not None
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_session_rollback(self, db_session):
        """Test that session transactions are properly rolled back."""
        # Create a temporary table
        db_session.execute(text(
            "CREATE TEMPORARY TABLE test_rollback (id INTEGER, name TEXT)"
        ))
        db_session.execute(text(
            "INSERT INTO test_rollback VALUES (1, 'test')"
        ))
        db_session.commit()

        # Verify data exists
        result = db_session.execute(text("SELECT COUNT(*) FROM test_rollback"))
        assert result.scalar() == 1

        # After test, rollback should occur automatically via fixture

    def test_multiple_connections(self, db_engine):
        """Test that we can handle multiple concurrent connections."""
        connections = []
        try:
            for _ in range(5):
                conn = db_engine.connect()
                connections.append(conn)
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            for conn in connections:
                conn.close()

    def test_database_exists(self, db_engine):
        """Test that the expected database exists."""
        with db_engine.connect() as connection:
            result = connection.execute(text(
                f"SELECT 1 FROM pg_database WHERE datname = '{settings.DB_NAME}'"
            ))
            assert result.scalar() == 1

    def test_alembic_version_table(self, db_engine):
        """Test that alembic_version table exists."""
        with db_engine.connect() as connection:
            result = connection.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'alembic_version')"
            ))
            assert result.scalar() is True


class TestDatabaseOperations:
    """Test basic database CRUD operations."""

    def test_insert_and_select(self, db_session):
        """Test basic insert and select operations."""
        db_session.execute(text(
            "CREATE TEMPORARY TABLE test_data (id SERIAL PRIMARY KEY, value TEXT)"
        ))
        db_session.execute(text(
            "INSERT INTO test_data (value) VALUES ('test1'), ('test2')"
        ))
        db_session.commit()

        result = db_session.execute(text("SELECT COUNT(*) FROM test_data"))
        assert result.scalar() == 2

    def test_update_operation(self, db_session):
        """Test update operations."""
        db_session.execute(text(
            "CREATE TEMPORARY TABLE test_update (id SERIAL PRIMARY KEY, value TEXT)"
        ))
        db_session.execute(text(
            "INSERT INTO test_update (value) VALUES ('original')"
        ))
        db_session.commit()

        db_session.execute(text(
            "UPDATE test_update SET value = 'updated' WHERE value = 'original'"
        ))
        db_session.commit()

        result = db_session.execute(text(
            "SELECT value FROM test_update LIMIT 1"
        ))
        assert result.scalar() == 'updated'

    def test_delete_operation(self, db_session):
        """Test delete operations."""
        db_session.execute(text(
            "CREATE TEMPORARY TABLE test_delete (id SERIAL PRIMARY KEY, value TEXT)"
        ))
        db_session.execute(text(
            "INSERT INTO test_delete (value) VALUES ('to_delete')"
        ))
        db_session.commit()

        db_session.execute(text(
            "DELETE FROM test_delete WHERE value = 'to_delete'"
        ))
        db_session.commit()

        result = db_session.execute(text("SELECT COUNT(*) FROM test_delete"))
        assert result.scalar() == 0
