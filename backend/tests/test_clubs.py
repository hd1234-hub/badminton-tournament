def register_user(client, username="clubtest"):
    return client.post("/api/v1/auth/register", json={
        "username": username, "password": "test123456", "name": "测试",
    }).json()["token"]


def test_create_club(client):
    token = register_user(client)
    resp = client.post("/api/v1/clubs", json={"name": "阳光羽毛球俱乐部"},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "阳光羽毛球俱乐部"
    assert data["owner_id"] is not None


def test_list_clubs(client):
    token = register_user(client)
    client.post("/api/v1/clubs", json={"name": "阳光羽毛球俱乐部"},
                headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/v1/clubs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_join_club(client):
    # 用户 A 创建俱乐部
    token_a = register_user(client, "user_a")
    club = client.post("/api/v1/clubs", json={"name": "测试俱乐部"},
                       headers={"Authorization": f"Bearer {token_a}"}).json()
    # 用户 B 加入
    token_b = register_user(client, "user_b")
    resp = client.post(f"/api/v1/clubs/{club['id']}/join",
                       headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200


def test_get_club_players(client):
    token = register_user(client)
    club = client.post("/api/v1/clubs", json={"name": "测试俱乐部"},
                       headers={"Authorization": f"Bearer {token}"}).json()
    resp = client.get(f"/api/v1/clubs/{club['id']}/players",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
