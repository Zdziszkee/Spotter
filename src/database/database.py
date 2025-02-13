from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class Database:
    Base = declarative_base()

    def __init__(self, url: str = 'sqlite:///database.db'):
        self.engine = create_engine(url, echo=True)  # echo=True will log SQL
        self._session_factory = sessionmaker(bind=self.engine)

    def create_all(self) -> None:
        """Create all tables."""
        # Import models here to avoid circular imports
        from src.models import street, offer

        # Drop all tables first (optional, remove if you want to preserve data)
        # self.Base.metadata.drop_all(self.engine)

        logger.info("Creating database tables...")
        self.Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {e}")
            session.rollback()
            raise
        finally:
            session.close()

# Global database instance
db = Database()
