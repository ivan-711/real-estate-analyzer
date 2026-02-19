"""
Pytest configuration and fixtures.

Fixtures:
- client: FastAPI TestClient for API tests
- test_user: Pre-created user with hashed password (for login tests)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend is in path for app imports
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Set test env vars before importing app (if not already set)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient for API tests."""
    from app.main import app

    return TestClient(app)
