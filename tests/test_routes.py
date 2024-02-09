import sys
from pathlib import Path
from typing import Generator

import pytest
from flask import request, url_for
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

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
            client.get("/")
            yield client
            db.session.remove()
            db.drop_all()


def create_user(
    client: FlaskClient,
    username: str,
    email_address: str,
    password1: str,
    password2: str,
) -> TestResponse:
    # After registration automatically logged in
    response = client.post(
        url_for("register_page"),
        data={
            "username": username,
            "email_address": email_address,
            "password1": password1,
            "password2": password2,
        },
        follow_redirects=True,
    )
    return response


def create_item(name: str, price: int, barcode: int, description: str) -> None:
    db.session.add(
        Item(
            name=name,
            price=price,
            barcode=barcode,
            description=description,
        )
    )
    db.session.commit()


@pytest.mark.parametrize(
    "func_path,exp_status_code,exp_text,exp_redirect",
    [
        # Test home page
        ("home_page", 200, b"Welcome to Jim Shaped Coding Market", "home_page"),
        # Test that we cannot access market page before logging
        ("market_page", 200, b"Register Page", "login_page"),
        # Test register page
        ("register_page", 200, b"Register Page", "register_page"),
        # Test login page
        ("login_page", 200, b"Register Page", "login_page"),
    ],
)
def test_simple_get(
    client: FlaskClient,
    func_path: str,
    exp_status_code: int,
    exp_text: str,
    exp_redirect: str,
) -> None:
    response = client.get(url_for(func_path), follow_redirects=True)

    # Check that we got the same code of response
    assert response.status_code == exp_status_code
    # Check whether we end on right page
    assert response.request.path == url_for(exp_redirect)
    # Check that required text data is displayed
    assert exp_text in response.data


@pytest.mark.parametrize(
    "username,email_address,password1,password2,exp_status_code,exp_redirect",
    [
        # Test POST with INVALID username
        ("t", "testuser@gmail.com", "qweqwe", "qweqwe", 200, "register_page"),
        # Test POST with INVALID email_address
        ("testuser", "testuser", "qweqwe", "qweqwe", 200, "register_page"),
        # Test POST with INVALID password confirmation
        ("testuser", "testuser@gmail.com", "qweqwe", "qwe", 200, "register_page"),
        # Test POST with VALID data
        ("testuser", "testuser@gmail.com", "qweqwe", "qweqwe", 200, "market_page"),
    ],
)
def test_registration_logic(
    client: FlaskClient,
    username: str,
    email_address: str,
    password1: str,
    password2: str,
    exp_status_code: int,
    exp_redirect: str,
) -> None:
    response = create_user(client, username, email_address, password1, password2)

    assert response.status_code == exp_status_code
    assert response.request.path == url_for(exp_redirect)


@pytest.mark.parametrize(
    "username,password,exp_status_code,exp_redirect",
    [
        # Test POST with INCORRECT username
        ("test1", "qweqwe", 200, "login_page"),
        # Test POST with INCORRECT password
        ("testuser1", "somepass", 200, "login_page"),
        # Test POST with CORRECT credentials
        ("testuser1", "qweqwe", 200, "market_page"),
    ],
)
def test_login_logic(
    client: FlaskClient,
    username: str,
    password: str,
    exp_status_code: int,
    exp_redirect: str,
) -> None:
    # Let's first of all register the user
    create_user(client, "testuser1", "testuser@gmail.com", "qweqwe", "qweqwe")

    response = client.post(
        url_for("login_page"),
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=True,
    )

    assert response.status_code == exp_status_code
    assert response.request.path == url_for(exp_redirect)


def test_logout_logic(client: FlaskClient) -> None:
    # Let's first of all register the user
    create_user(client, "testuser1", "testuser@gmail.com", "qweqwe", "qwewe")

    # Check that user is able to log out
    response = client.get(url_for("logout_page"), follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == url_for("home_page")


@pytest.mark.parametrize(
    "username,email_address,password1,password2,exp_status_code,exp_redirect",
    [
        # Test that we cannot create user with existing username
        ("testuser1", "testuser2@gmail.com", "qweqwe", "qweqwe", 200, "register_page"),
        # Test that we cannot create user with existing email_address
        ("testuser2", "testuser@gmail.com", "qweqwe", "qweqwe", 200, "register_page"),
    ],
)
def test_forms_validations(
    client: FlaskClient,
    username: str,
    email_address: str,
    password1: str,
    password2: str,
    exp_status_code: int,
    exp_redirect: str,
) -> None:
    # Let's first of all register the user
    create_user(client, "testuser1", "testuser@gmail.com", "qweqwe", "qweqwe")

    response = client.post(
        url_for("register_page"),
        data={
            "username": username,
            "email_address": email_address,
            "password1": password1,
            "password2": password2,
        },
        follow_redirects=True,
    )

    assert response.status_code == exp_status_code
    assert response.request.path == url_for(exp_redirect)


@pytest.mark.parametrize(
    "item_name,price,barcode,description,exp_balance_after_buy,exp_balance_after_sell,"
    "num_after_buy,num_after_sell,exp_status_code",
    [
        # Test that user cannot buy product with insufficient balance
        # and that (s)he cannot sell product (s)he does not own
        ("Expensive", 10000, 111000111, "desc", b"1,000", b"1,000", 0, 0, 200),
        # Test that user can buy product with sufficient balance
        # and that (s)he can sell product (s)he does own
        ("Cheap", 500, 111000112, "desc", b"500", b"1,000", 1, 0, 200),
    ],
)
def test_market_logic(
    client: FlaskClient,
    item_name: str,
    price: int,
    barcode: int,
    description: str,
    exp_balance_after_buy: str,
    exp_balance_after_sell: str,
    num_after_buy: int,
    num_after_sell: int,
    exp_status_code: int,
) -> None:
    # Remark: by the way, here we check that balance is displayed correctly
    # according to our logic

    # Let's first of all register the user (budget==1000, by default)
    create_user(client, "testuser1", "testuser@gmail.com", "qweqwe", "qweqwe")
    user = User.query.filter_by(username="testuser1").first()

    # Push products to the market
    create_item(
        name=item_name,
        price=price,
        barcode=barcode,
        description=description,
    )

    response = client.post(
        url_for("market_page"),
        data={"purchased_item": item_name},
        follow_redirects=True,
    )
    assert response.status_code == exp_status_code
    assert exp_balance_after_buy in response.data
    assert len(user.items) == num_after_buy

    response = client.post(
        url_for("market_page"),
        data={"sold_item": item_name},
        follow_redirects=True,
    )
    assert response.status_code == exp_status_code
    assert exp_balance_after_sell in response.data
    assert len(user.items) == num_after_sell


def test_minor_logic(client: FlaskClient) -> None:
    # Check that item is displayed correctly
    create_item(
        name="Random item",
        price=500,
        barcode=111000111,
        description="Random item desc",
    )
    item = Item.query.filter_by(name="Random item").first()
    assert item.__repr__() == f"Item {item.name}"
