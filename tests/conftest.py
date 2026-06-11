"""conftest.py — point the app at a throwaway test database.

DATABASE_URL must be set before database.py is first imported, because the
engine binds at import time. A file-backed test DB (not :memory:) is used so
multiple sessions in one test see the same data.
"""

from __future__ import annotations

import os
import pathlib
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_cfius_screener.db"

# Tests run from anywhere; make the project root importable.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    import models  # noqa: F401 — register tables before create_all
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
