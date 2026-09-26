from collections.abc import Generator
import ssl

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()

connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }

elif settings.database_url.startswith("postgresql+pg8000"):
    # Neon PostgreSQL requires an encrypted connection.
    # pg8000 expects an SSLContext rather than psycopg's sslmode parameter.
    connect_args = {
        "ssl_context": ssl.create_default_context(),
    }


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()