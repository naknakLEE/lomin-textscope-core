import pytest

from fastapi.testclient import TestClient
from fastapi.security import OAuth2, OAuth2PasswordRequestFormStrict
from fastapi import Depends, FastAPI, Security

from app.utils.create_app import app_generator

app = app_generator()
client = TestClient(app)



@app.post("/login")
# Here we use string annotations to test them
def login(form_data: "OAuth2PasswordRequestFormStrict" = Depends()):
    return form_data



# def test_security_oauth2():
#     response = client.get("/users/me", headers={"Authorization": "Bearer footokenbar"})
#     assert response.status_code == 200, response.text
#     assert response.json() == {"username": "Bearer footokenbar"}

required_params = {
    "detail": [
        {
            "loc": ["body", "grant_type"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", "username"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", "password"],
            "msg": "field required",
            "type": "value_error.missing",
        },
    ]
}


grant_type_required = {
    "detail": [
        {
            "loc": ["body", "grant_type"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
}

grant_type_incorrect = {
    "detail": [
        {
            "loc": ["body", "grant_type"],
            "msg": 'string does not match regex "password"',
            "type": "value_error.str.regex",
            "ctx": {"pattern": "password"},
        }
    ]
}

@pytest.mark.parametrize(
    "data,expected_status,expected_response",
    [
        (None, 422, required_params),
        ({"username": "johndoe", "password": "secret"}, 422, grant_type_required),
        (
            {"username": "johndoe", "password": "secret", "grant_type": "incorrect"},
            422,
            grant_type_incorrect,
        ),
        (
            {"username": "johndoe", "password": "secret", "grant_type": "password"},
            200,
            {
                "grant_type": "password",
                "username": "johndoe",
                "password": "secret",
                "scopes": [],
                "client_id": None,
                "client_secret": None,
            },
        ),
    ],
)
def test_strict_login(data, expected_status, expected_response):
    response = client.post("/v1/auth/token", data=data)
    assert response.status_code == expected_status
    assert response.json() == expected_response