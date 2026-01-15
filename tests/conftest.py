import pytest
from flask import Flask
from flask import request as flask_request


@pytest.fixture
def client():
    import main

    app = Flask(__name__)
    app.config["TESTING"] = True

    app.add_url_rule(
        "/",
        view_func=lambda: main.start(flask_request),
        methods=["POST", "OPTIONS"],
    )

    return app.test_client()
