"""Base repository class with common database operations."""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.base import Base

# Define generic types
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        """Initialize repository with a SQLAlchemy model."""
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record."""
        obj_data = obj_in.dict(exclude_unset=True) if not isinstance(obj_in, dict) else obj_in
        
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """Delete a record."""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def get_by_field(
        self, db: Session, *, field: str, value: Any
    ) -> Optional[ModelType]:
        """Get a record by a specific field."""
        return db.query(self.model).filter(getattr(self.model, field) == value).first()

    def get_multi_by_field(
        self, db: Session, *, field: str, value: Any, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records by a specific field."""
        return (
            db.query(self.model)
            .filter(getattr(self.model, field) == value)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_or_create(
        self, db: Session, *, defaults: Optional[Dict[str, Any]] = None, **kwargs
    ) -> tuple[ModelType, bool]:
        """Get a record or create it if it doesn't exist."""
        instance = db.query(self.model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            params = {**kwargs, **(defaults or {})}
            instance = self.model(**params)  # type: ignore
            db.add(instance)
            db.commit()
            db.refresh(instance)
            return instance, True
