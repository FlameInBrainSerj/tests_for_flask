import sys
from pathlib import Path
from typing import Generator

import pytest
from flask import request, url_for
from flask.testing import FlaskClient

# It must be here!!! (cannot replace import)
sys.path.append(str(Path().cwd()))
from market import app, db


@pytest.fixture()
def client() -> Generator[FlaskClient, None, None]:
    app.config["TESTING"] = True
    app.config["WTF_CSRF_METHODS"] = {}
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_home_page(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")

    # Test GET by /
    response = client.get("/")
    assert response.status_code == 200
    assert request.path == "/"
    assert b"Welcome to Jim Shaped Coding Market" in response.data

    # Test GET by /home
    response = client.get(url_for("home_page"))
    assert response.status_code == 200
    assert request.path == url_for("home_page")
    assert b"Welcome to Jim Shaped Coding Market" in response.data


def test_registration(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")

    # Test GET
    response = client.get(url_for("register_page"))
    assert response.status_code == 200
    assert b"Register Page" in response.data

    # Test POST with INVALID username
    response = client.post(
        url_for("register_page"),
        data={
            "username": "t",
            "email_address": "testuser2@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("register_page")

    # Test POST with INVALID email_address
    response = client.post(
        url_for("register_page"),
        data={
            "username": "testuser3",
            "email_address": "ttt@g",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("register_page")

    # Test POST with INVALID password confirmation
    response = client.post(
        url_for("register_page"),
        data={
            "username": "testuser3",
            "email_address": "testuser3@gmail.com",
            "password1": "qweqwe",
            "password2": "qwe",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("register_page")

    # Test POST with VALID data
    response = client.post(
        url_for("register_page"),
        data={
            "username": "testuser1",
            "email_address": "testuser1@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we were redirected to the url_for("market_page")
    assert response.status_code == 200
    assert response.request.path == url_for("market_page")


def test_login_and_logout(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")

    # Let's first of all register the user
    response = client.post(
        url_for("register_page"),
        data={
            "username": "testuser1",
            "email_address": "testuser1@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we were redirected to the url_for("market_page")
    assert response.status_code == 200
    assert response.request.path == url_for("market_page")

    # Check that we are able to log out
    response = client.get(url_for("logout_page"), follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == url_for("home_page")

    # Test GET
    response = client.get(url_for("login_page"))
    assert response.status_code == 200
    assert b"Register Page" in response.data

    # Test POST with INCORRECT username
    response = client.post(
        url_for("login_page"),
        data={
            "username": "test1",
            "password": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("login_page")

    # Test POST with INCORRECT password
    response = client.post(
        url_for("login_page"),
        data={
            "username": "test1",
            "password": "somepass",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("login_page")

    # Test POST with CORRECT credentials
    response = client.post(
        url_for("login_page"),
        data={
            "username": "testuser1",
            "password": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we were redirected to url_for("market_page")
    assert response.status_code == 200
    assert response.request.path == url_for("market_page")


def test_forms_validations(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")
    pass


def test_market_logic(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")
    pass
