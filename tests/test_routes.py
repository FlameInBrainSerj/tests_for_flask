import sys
from pathlib import Path
from typing import Generator

import pytest
from flask import request, url_for
from flask.testing import FlaskClient

# It must be here!!! (cannot replace import)
sys.path.append(str(Path().cwd()))
from market import Item, User, app, db


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


def test_registration_logic(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")

    # Test that we cannot access url_for("market_page") before
    # registration or logging in
    response = client.get(url_for("market_page"), follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == url_for("login_page")

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


def test_login_and_logout_logic(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")

    # Let's first of all register the user
    client.post(
        url_for("register_page"),
        data={
            "username": "testuser1",
            "email_address": "testuser1@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )

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

    client.post(
        url_for("register_page"),
        data={
            "username": "testuser1",
            "email_address": "testuser1@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )

    # Check that we cannot create user with existing username
    response = client.post(
        url_for("register_page"),
        data={
            "username": "testuser1",
            "email_address": "testuser2@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("register_page")

    # Check that we cannot create user with existing email_address
    response = client.post(
        url_for("register_page"),
        data={
            "username": "testuser2",
            "email_address": "testuser1@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    # Check that we are still on the same page
    assert response.status_code == 200
    assert response.request.path == url_for("register_page")


def test_market_logic(client: FlaskClient) -> None:
    # Remark: by the way, here we check that balance is displayed correctly
    # according to our logic

    # Just let it be here :)
    client.get("/")

    # First of all wes need to push some products to the market
    db.session.add(
        Item(
            name="Expensive",
            price=10000,
            barcode=111000111,
            description="Expensive item desc",
        )
    )
    db.session.add(
        Item(name="Cheap", price=500, barcode=111000112, description="Cheap item desc")
    )
    db.session.commit()

    # Register the user
    client.post(
        url_for("register_page"),
        data={
            "username": "testuser1",
            "email_address": "testuser1@gmail.com",
            "password1": "qweqwe",
            "password2": "qweqwe",
        },
        follow_redirects=True,
    )
    user = User.query.filter_by(username="testuser1").first()

    # Test POST (purchase) with insufficient balance
    response = client.post(
        url_for("market_page"),
        data={"purchased_item": "Expensive"},
        follow_redirects=True,
    )
    # Check that the balance stayed the same and no items were added to the user
    assert b"1,000" in response.data
    assert len(user.items) == 0

    # Test POST (purchase) with sufficient balance
    response = client.post(
        url_for("market_page"),
        data={"purchased_item": "Cheap"},
        follow_redirects=True,
    )
    # Check that the balance decreased correctly and one item was added to user
    assert b"500" in response.data
    assert len(user.items) == 1

    # Test POST (sell) with the product user do not have
    response = client.post(
        url_for("market_page"),
        data={"sold_item": "Expensive"},
        follow_redirects=True,
    )
    # Check that the balance stayed the same and no items were sold
    assert b"500" in response.data
    assert len(user.items) == 1

    # Test POST (sell) with the product user has
    response = client.post(
        url_for("market_page"),
        data={"sold_item": "Cheap"},
        follow_redirects=True,
    )
    # Check that the balance increased correctly and one item was sold
    assert b"1,000" in response.data
    assert len(user.items) == 0


def test_minor_logic(client: FlaskClient) -> None:
    # Just let it be here :)
    client.get("/")

    # Check that item is displayed correctly
    db.session.add(
        Item(
            name="Random item",
            price=500,
            barcode=111000111,
            description="Random item desc",
        )
    )
    db.session.commit()
    item = Item.query.filter_by(name="Random item").first()
    assert item.__repr__() == f"Item {item.name}"
