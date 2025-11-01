"""Base SQLAlchemy model class with common functionality."""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

@as_declarative()
class Base:
    """Base class for all database models."""

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically.
        
        Returns:
            str: The table name in snake_case
        """
        return cls.__name__.lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    @classmethod
    def get_by_id(cls, db: Session, id: int) -> Optional[Any]:
        """Get a model instance by ID.
        
        Args:
            db: Database session
            id: ID of the instance to retrieve
            
        Returns:
            Optional[Any]: The model instance if found, None otherwise
        """
        return db.query(cls).filter(cls.id == id).first()

    def save(self, db: Session) -> None:
        """Save the model instance to the database.
        
        Args:
            db: Database session
        """
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session) -> None:
        """Delete the model instance from the database.
        
        Args:
            db: Database session
        """
        db.delete(self)
        db.commit()

    def update(self, db: Session, **kwargs) -> None:
        """Update the model instance with the given attributes.
        
        Args:
            db: Database session
            **kwargs: Attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save(db)
