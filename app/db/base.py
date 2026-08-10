from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 Base class for ORM models.
    All database models will inherit from this base class.
    """

    pass
