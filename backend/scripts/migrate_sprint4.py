"""Idempotently create Sprint 4 tables and indexes; never alters existing data."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import models  # noqa: F401
from app.database import Base,engine
if __name__=="__main__":
    Base.metadata.create_all(bind=engine)
    print("Sprint 4 schema is present (non-destructive, idempotent).")
