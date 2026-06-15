from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS category_id INTEGER "
                "REFERENCES categories(id)"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE generated_images ADD COLUMN IF NOT EXISTS "
                "visual_brief TEXT"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE generated_images ADD COLUMN IF NOT EXISTS "
                "model VARCHAR(64)"
            )
        )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
