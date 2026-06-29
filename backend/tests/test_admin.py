def _register(client, username: str, password: str = "test123456", name: str = "测试"):
    res = client.post("/api/v1/auth/register", json={
        "username": username,
        "password": password,
        "name": name,
    })
    assert res.status_code == 200, res.text
    return res.json()


def test_admin_forbidden_for_normal_user(client):
    data = _register(client, "normal_user_admin_test")
    token = data["token"]
    res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_admin_stats_for_admin_user(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.admin_usernames", "admin_user_test")
    data = _register(client, "admin_user_test", name="管理员")
    assert data["user"]["is_admin"] is True
    token = data["token"]

    res = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["total_users"] >= 1
    assert "today_registrations" in body

    trend = client.get("/api/v1/admin/stats/registrations", headers={"Authorization": f"Bearer {token}"})
    assert trend.status_code == 200
    assert isinstance(trend.json(), list)

    users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert users.status_code == 200
    assert users.json()["total"] >= 1
