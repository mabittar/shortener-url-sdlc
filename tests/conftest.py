"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def test_client():
    """Provide a test client for API tests."""
    from fastapi.testclient import TestClient
    from src.main import app

    return TestClient(app)
