from fastapi.testclient import TestClient

def test_wechat_login_for_new_user(client: TestClient):
    test_code = "some-test-code"
    response = client.post("/api/v1/auth/wechat", json={"code": test_code})
    assert response.status_code == 200
    assert "access_token" in response.json()