from tests.test_competitions import register_and_create_club, add_players


def test_leaderboard(client):
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})

    resp = client.get(f"/api/v1/leaderboard?club_id={club['id']}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 9  # 创建者(测试用户) + 8 名添加的球员
    assert len(data["entries"]) == 9
