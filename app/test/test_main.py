import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, drop_database, database_exists

import main
from app.database import Base, get_db, SQLALCHEMY_DATABASE_URL
from app import auth, routes

# Replace with your test PostgreSQL connection URL

TEST_DATABASE_URL = "postgresql://ubuntu:ubuntu@localhost:5432/test"

# Override the original database URL with the test database URL
SQLALCHEMY_DATABASE_URL = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def app():
    # Create a new test database
    if not database_exists(TEST_DATABASE_URL):
        create_database(TEST_DATABASE_URL)

    # Create tables in the test database
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    # Create a session for the test database
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine)
    main.SessionLocal = TestingSessionLocal

    # Create the FastAPI application
    app = FastAPI()

    # Add the application routes
    main.app.include_router(auth.router)
    main.app.include_router(routes.router)

    yield app

    # Drop the test database after all tests are done
    drop_database(TEST_DATABASE_URL)


@pytest.fixture
def client(app):
    # Create a test client for the FastAPI application
    return TestClient(app)


def test_register_user(client):
    # Send a POST request to the /register endpoint to register a new user
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )

    # Check that the request was successful (status code 200) and the response data matches the expected values
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_login_and_access_protected_route(client):
    # Register a new user
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200

    # Send a POST request to the /token endpoint to obtain an access token
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200

    access_token = response.json()["access_token"]

    # Send a GET request to the protected /users/me endpoint with the access token in the Authorization header
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/me", headers=headers)

    # Check that the request was successful (status code 200) and the response data matches the expected values
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

    # Send a GET request to the protected /users/me endpoint without the access token
    response = client.get("/users/me")

    # Check that the request is unauthorized (status code 401)
    assert response.status_code == 401


def test_refresh_token(client):
    # Register a new user
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200

    # Send a POST request to the /token endpoint to obtain an access token and refresh token
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200

    refresh_token = response.json()["refresh_token"]

    # Send a POST request to the /refresh-token endpoint to obtain a new access token using the refresh token
    response = client.post(
        "/refresh-token",
        data={"refresh_token": refresh_token}
    )
    assert response.status_code == 200

    access_token = response.json()["access_token"]

    # Send a GET request to the protected /users/me endpoint with the new access token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/me", headers=headers)

    # Check that the request was successful (status code 200) and the response data matches the expected values
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
