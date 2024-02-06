import sys
from pathlib import Path
from typing import Generator

import pytest
from flask import render_template
from flask.testing import FlaskClient

# It must be here!!! (cannot replace import)
sys.path.append(str(Path().cwd()))
from market import app


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    with app.test_client() as client:
        yield client


def test_home_page(client: FlaskClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    # assert b'home.html' in response.data

    response = client.get("/home")
    assert response.status_code == 200
    # assert b'home.html' in response.data
