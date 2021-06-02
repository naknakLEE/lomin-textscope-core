from fastapi.testclient import TestClient

def test_read_items(client: TestClient):
    response = client.get("/items/foo")
    assert response.status_code == 200
    assert response.json() == {"name": "Fighters"}