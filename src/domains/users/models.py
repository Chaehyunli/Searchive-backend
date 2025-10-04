from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from src.db.session import Base


class User(Base):
    """User model for authentication and user management"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    def __repr__(self):
        return f"<User(id={self.id})>"
