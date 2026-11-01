"""Database initialisation — creates tables if they don't exist."""
from app.database.base import Base, engine
from app.models import models  # noqa: F401 — registers models with Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
