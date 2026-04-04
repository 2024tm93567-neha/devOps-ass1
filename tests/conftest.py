"""
Pytest configuration and shared fixtures for the ACEest test suite.

Strategy
--------
Each test *session* gets a temporary SQLite file.  Using a real file (rather
than ``:memory:``) means every call to ``get_db()`` inside the app operates on
the *same* database, which is how the production code works.  The file is
deleted automatically after the session ends.
"""

import os
import tempfile

import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    """
    Create a Flask application configured for testing.

    - Uses a temporary on-disk SQLite file (same isolation as production).
    - Sets TESTING=True so Flask propagates exceptions to the test runner.
    - Cleans up the temp file after the full session completes.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    flask_app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
        }
    )

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="session")
def client(app):
    """Return a Flask test client bound to the session-scoped app."""
    return app.test_client()
