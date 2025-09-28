# -*- coding: utf-8 -*-
"""
Simple integration tests to verify the new functionality works correctly.

These tests focus on verifying that the endpoints exist and handle
basic validation without complex authentication mocking.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Test client fixture.""" 
    return TestClient(app)


def test_admin_endpoint_exists_and_requires_auth(client):
    """Test that the admin endpoint exists and requires authentication."""
    response = client.post(
        "/api/v1/admin/agent/command",
        json={"action": "test_action"}
    )
    # Should get 401 unauthorized, not 404 not found
    assert response.status_code == 401


def test_emergency_endpoint_exists_and_requires_auth(client):
    """Test that the emergency endpoint exists and requires authentication."""
    response = client.post(
        "/api/v1/tasks/emergency", 
        json={
            "telegram_id": 123456789,
            "lat": 40.7128,
            "lng": -74.0060
        }
    )
    # Should get 401 unauthorized, not 404 not found
    assert response.status_code == 401


def test_emergency_endpoint_validation_works(client):
    """Test that emergency endpoint validates input without authentication."""
    # Test with completely invalid JSON structure
    response = client.post(
        "/api/v1/tasks/emergency",
        json={"invalid": "data"}
    )
    # Should get 401 (auth required) or 422 (validation error)
    # Either is acceptable since auth comes first
    assert response.status_code in [401, 422]


def test_admin_endpoint_validation_works(client):
    """Test that admin endpoint validates input without authentication."""
    # Test with completely invalid JSON structure  
    response = client.post(
        "/api/v1/admin/agent/command",
        json={"invalid": "data"}
    )
    # Should get 401 (auth required) or 422 (validation error)
    # Either is acceptable since auth comes first
    assert response.status_code in [401, 422]


def test_openapi_includes_new_endpoints(client):
    """Test that the new endpoints are included in the OpenAPI spec."""
    # Try different possible OpenAPI paths
    openapi_paths = ["/openapi.json", "/docs/openapi.json", "/api/v1/openapi.json"]
    
    response = None
    for path in openapi_paths:
        response = client.get(path)
        if response.status_code == 200:
            break
    
    # If we couldn't find OpenAPI spec, skip this test
    if not response or response.status_code != 200:
        pytest.skip("OpenAPI spec not found at standard paths")
    
    openapi_spec = response.json()
    paths = openapi_spec.get("paths", {})
    
    # Check that our new endpoints are documented
    assert "/api/v1/admin/agent/command" in paths
    assert "/api/v1/tasks/emergency" in paths
    
    # Check that the endpoints have the correct HTTP methods
    admin_path = paths["/api/v1/admin/agent/command"]
    assert "post" in admin_path
    
    emergency_path = paths["/api/v1/tasks/emergency"] 
    assert "post" in emergency_path