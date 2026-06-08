from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(
    f"iris://{settings.iris_username}:{settings.iris_password}@"
    f"{settings.iris_host}:{settings.iris_port}/{settings.iris_namespace}"
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_schema_if_not_exists(engine):
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE SCHEMA labcore")
            conn.commit()
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
