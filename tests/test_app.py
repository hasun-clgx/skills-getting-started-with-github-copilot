from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


BASELINE_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture
def activity_data(monkeypatch):
    isolated_activities = deepcopy(BASELINE_ACTIVITIES)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activity_data):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data_without_caching(client, activity_data):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activity_data
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in activity_data["Chess Club"]["participants"]
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client, activity_data):
    # Arrange
    email = "new.student@mergington.edu"
    activity_data["Chess Club"]["participants"].append(email)

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activity_data["Chess Club"]["participants"].count(email) == 1


def test_signup_requires_email(client):
    # Arrange

    # Act
    response = client.post("/activities/Chess Club/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    email = "michael@mergington.edu"
    assert email in activity_data["Chess Club"]["participants"]

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in activity_data["Chess Club"]["participants"]
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"