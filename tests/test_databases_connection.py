#!/usr/bin/env python3
import sys
import pathlib
import types

# Ensure project root is on sys.path when running the script directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import databases


def test_database_connection_importable():
    assert callable(databases.test_connection)


def test_database_connection_returns_true_when_db_responds(monkeypatch):
    class DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, q):
            pass

        def fetchone(self):
            return {"ok": 1}

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self, row_factory=None):
            return DummyCursor()
    # Ensure DATABASE_URL is present so `test_connection` reads it at call time
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

    # Create a minimal fake psycopg package (and psycopg.rows) for the test
    psy_mod = types.ModuleType("psycopg")
    psy_rows = types.ModuleType("psycopg.rows")
    psy_rows.dict_row = None
    psy_mod.rows = psy_rows
    psy_mod.connect = lambda *a, **k: DummyConn()

    monkeypatch.setitem(sys.modules, "psycopg", psy_mod)
    monkeypatch.setitem(sys.modules, "psycopg.rows", psy_rows)

    assert databases.test_connection() is True


if __name__ == "__main__":
    # Direct-run fallback: inject fake psycopg and run the check
    class DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, q):
            pass

        def fetchone(self):
            return {"ok": 1}

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self, row_factory=None):
            return DummyCursor()

    psy_mod = types.ModuleType("psycopg")
    psy_rows = types.ModuleType("psycopg.rows")
    psy_rows.dict_row = None
    psy_mod.rows = psy_rows
    psy_mod.connect = lambda *a, **k: DummyConn()

    sys.modules.setdefault("psycopg", psy_mod)
    sys.modules.setdefault("psycopg.rows", psy_rows)

    ok = test_connection()
    print("tests/test_databases_connection.py -> test_connection() returned:", ok)
