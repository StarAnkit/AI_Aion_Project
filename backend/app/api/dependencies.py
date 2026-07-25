from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import create_database_engine, create_session_factory


def get_catalog_session() -> Generator[Session, None, None]:
    """Open a database session only for catalog endpoints that need one."""
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        yield session
