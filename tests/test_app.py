from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_activity_data(client):
    # Arrange
    activity_name = "Soccer Team"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name]["participants"] == []


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "new-student@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    participant_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert len(activities[activity_name]["participants"]) == participant_count


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404


def test_delete_removes_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "registered-student@example.com"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_delete_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404


def test_delete_returns_404_for_unregistered_participant(client):
    # Arrange
    activity_name = "Soccer Team"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "not-registered@example.com"},
    )

    # Assert
    assert response.status_code == 404


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location