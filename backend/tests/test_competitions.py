def register_and_create_club(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "comptest", "password": "test123456", "name": "比赛测试",
    })
    token = resp.json()["token"]
    club = client.post("/api/v1/clubs", json={"name": "测试俱乐部"},
                       headers={"Authorization": f"Bearer {token}"}).json()
    return token, club


def add_players(client, token, club_id, count=8):
    pids = []
    for i in range(count):
        resp = client.post("/api/v1/players", json={"name": f"球员{i+1}"},
                           headers={"Authorization": f"Bearer {token}"})
        pid = resp.json()["id"]
        client.post(f"/api/v1/clubs/{club_id}/players/{pid}",
                    headers={"Authorization": f"Bearer {token}"})
        pids.append(pid)
    return pids


def test_create_eight_player_competition(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    resp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "周日八人转"
    assert len(data["rounds"]) == 7
    assert data["status"] == "pending"


def test_start_competition(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    resp = client.patch(f"/api/v1/competitions/{comp['id']}/start",
                        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_record_score(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})
    match_id = comp["rounds"][0]["matches"][0]["id"]
    resp = client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 21, "score_b": 15,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["score_a"] == 21
    assert resp.json()["score_b"] == 15


def test_duplicate_score_rejected(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})
    match_id = comp["rounds"][0]["matches"][0]["id"]
    client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 21, "score_b": 15,
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 19, "score_b": 21,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_invalid_score_rejected(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})
    match_id = comp["rounds"][0]["matches"][0]["id"]
    for score_a, score_b in [(30, 0), (21, 24)]:
        resp = client.post(f"/api/v1/matches/{match_id}/score", json={
            "score_a": score_a, "score_b": score_b,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400


def test_deuce_final_score_allowed(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})
    match_id = comp["rounds"][0]["matches"][0]["id"]
    resp = client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 21, "score_b": 23,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["score_a"] == 21
    assert resp.json()["score_b"] == 23


def test_leave_open_competition(client):
    token, club = register_and_create_club(client)
    comp = client.post("/api/v1/competitions", json={
        "name": "大厅测试", "club_id": None,
        "format": "singles_rotation", "courts": 1,
        "player_ids": [], "open_signup": True, "is_public": True,
        "max_players": 2,
    }, headers={"Authorization": f"Bearer {token}"}).json()
    # 创建者已自动报名，直接退赛
    resp = client.delete(
        f"/api/v1/competitions/{comp['id']}/join",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    detail = client.get(
        f"/api/v1/competitions/{comp['id']}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert len(detail["players"]) == 0

