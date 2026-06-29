def test_register(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "player1", "password": "test123456", "name": "张三",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["name"] == "张三"
    assert "token" in data


def test_login(client):
    client.post("/api/v1/auth/register", json={
        "username": "player2", "password": "test123456", "name": "李四",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "player2", "password": "test123456",
    })
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "username": "player3", "password": "test123456", "name": "王五",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "player3", "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_me(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "player4", "password": "test123456", "name": "赵六",
    })
    token = resp.json()["token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "player4"
