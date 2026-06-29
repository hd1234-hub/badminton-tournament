#!/usr/bin/env python3
"""Live integration test against running backend + PostgreSQL."""

import json
import sys
import time
import uuid

import httpx

BASE = "http://127.0.0.1:8000"
SUFFIX = uuid.uuid4().hex[:8]


def ok(msg: str):
    print(f"  [OK] {msg}")


def fail(msg: str):
    print(f"  [FAIL] {msg}")
    return False


def section(title: str):
    print(f"\n=== {title} ===")


class LiveTest:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE, timeout=30.0)
        self.users: dict[str, dict] = {}
        self.errors: list[str] = []
        self.club_id: int | None = None
        self.comp_id: int | None = None
        self.player_ids: list[int] = []

    def register(self, key: str, username: str, name: str) -> str | None:
        r = self.client.post("/api/v1/auth/register", json={
            "username": username,
            "password": "test123456",
            "name": name,
            "gender": "male",
            "skill_level": 3,
            "birth_year": 1995,
            "bio": "auto test user",
        })
        if r.status_code != 200:
            self.errors.append(f"register {username}: {r.status_code} {r.text[:200]}")
            return None
        data = r.json()
        self.users[key] = {"token": data["token"], "user": data["user"], "name": name}
        ok(f"注册用户 {name} ({username}) id={data['user']['id']}")
        return data["token"]

    def auth(self, key: str) -> dict:
        return {"Authorization": f"Bearer {self.users[key]['token']}"}

    def run(self) -> int:
        section("1. Health")
        r = self.client.get("/api/v1/health")
        if r.status_code != 200:
            print("后端未启动，请先启动 uvicorn")
            return 1
        ok(f"health -> {r.json()}")

        section("2. 创建3个测试账号")
        self.register("alice", f"alice_{SUFFIX}", "爱丽丝")
        self.register("bob", f"bob_{SUFFIX}", "鲍勃")
        self.register("carol", f"carol_{SUFFIX}", "卡罗尔")
        if len(self.users) < 3:
            return 1

        section("3. 俱乐部：创建 + 加入 + 添加球员")
        r = self.client.post("/api/v1/clubs", json={"name": f"测试俱乐部_{SUFFIX}"}, headers=self.auth("alice"))
        if r.status_code != 200:
            self.errors.append(f"create club: {r.text}")
            return 1
        club = r.json()
        self.club_id = club["id"]
        ok(f"创建俱乐部 id={self.club_id}")

        r = self.client.post(f"/api/v1/clubs/{self.club_id}/join", headers=self.auth("bob"))
        if r.status_code != 200:
            self.errors.append(f"bob join: {r.text}")
        else:
            ok("鲍勃加入俱乐部")

        r = self.client.post(f"/api/v1/clubs/{self.club_id}/join", headers=self.auth("carol"))
        if r.status_code != 200:
            self.errors.append(f"carol join: {r.text}")
        else:
            ok("卡罗尔加入俱乐部")

        # 添加额外球员凑八人转
        for i in range(5):
            r = self.client.post("/api/v1/players", json={"name": f"球员{i+1}_{SUFFIX}"}, headers=self.auth("alice"))
            if r.status_code == 200:
                pid = r.json()["id"]
                self.client.post(f"/api/v1/clubs/{self.club_id}/players/{pid}", headers=self.auth("alice"))
                self.player_ids.append(pid)

        r = self.client.get(f"/api/v1/clubs/{self.club_id}/players", headers=self.auth("alice"))
        players = r.json()
        ok(f"俱乐部成员数: {len(players)}")
        if len(players) < 8:
            self.errors.append(f"球员不足8人: {len(players)}")

        pids = [p["id"] for p in players[:8]]

        section("4. 比赛：创建八人转 + 开始 + 录分")
        r = self.client.post("/api/v1/competitions", json={
            "name": f"周日八人转_{SUFFIX}",
            "club_id": self.club_id,
            "format": "eight_player_rotation",
            "courts": 2,
            "player_ids": pids,
        }, headers=self.auth("alice"))
        if r.status_code != 200:
            self.errors.append(f"create competition: {r.text}")
            return 1
        comp = r.json()
        self.comp_id = comp["id"]
        ok(f"创建比赛 id={self.comp_id}, 轮次={len(comp['rounds'])}")

        if len(comp["rounds"]) != 7:
            self.errors.append(f"八人转应有7轮, 实际{len(comp['rounds'])}")

        r = self.client.patch(f"/api/v1/competitions/{self.comp_id}/start", headers=self.auth("alice"))
        if r.status_code != 200 or r.json()["status"] != "in_progress":
            self.errors.append(f"start competition: {r.text}")
        else:
            ok("比赛已开始")

        match_id = comp["rounds"][0]["matches"][0]["id"]
        r = self.client.post(f"/api/v1/matches/{match_id}/score", json={"score_a": 21, "score_b": 15}, headers=self.auth("alice"))
        if r.status_code != 200:
            self.errors.append(f"record score: {r.text}")
        else:
            ok(f"录入比分 match#{match_id} -> 21:15")

        section("5. 排行榜")
        r = self.client.get(f"/api/v1/leaderboard?club_id={self.club_id}", headers=self.auth("alice"))
        if r.status_code == 200:
            data = r.json()
            ok(f"排行榜条目数: {data.get('total', len(data.get('entries', [])))}")
        else:
            self.errors.append(f"leaderboard: {r.text}")

        section("6. AI Agent 测试")
        self.test_agent()

        section("7. PostgreSQL 数据校验")
        self.check_db()

        section("总结")
        if self.errors:
            print(f"\n发现 {len(self.errors)} 个问题:")
            for e in self.errors:
                print(f"  - {e}")
            return 1
        print("\n全部测试通过!")
        print(f"\n测试账号密码均为: test123456")
        print(f"  alice_{SUFFIX} / bob_{SUFFIX} / carol_{SUFFIX}")
        print(f"俱乐部ID: {self.club_id}, 比赛ID: {self.comp_id}")
        return 0

    def test_agent(self):
        r = self.client.post(
            "/api/v1/agent/chat",
            json={"message": "你好，帮我看看我有哪些俱乐部", "history": []},
            headers=self.auth("alice"),
            timeout=60.0,
        )
        if r.status_code != 200:
            self.errors.append(f"agent chat HTTP {r.status_code}")
            return

        body = r.text
        events = []
        for line in body.split("\n"):
            if line.startswith("data: "):
                try:
                    events.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    pass

        types = [e.get("type") for e in events]
        if "start" not in types:
            self.errors.append("agent: 缺少 start 事件")
        if "error" in types:
            err = next(e for e in events if e.get("type") == "error")
            self.errors.append(f"agent error: {err.get('content', err)}")
            print(f"  [WARN] AI返回错误: {err.get('content', '')[:100]}")
            return
        if "done" not in types:
            self.errors.append("agent: 缺少 done 事件 (可能超时)")
            return

        texts = [e.get("content", "") for e in events if e.get("type") == "text"]
        tool_calls = [e for e in events if e.get("type") == "tool_call"]
        ok(f"AI响应: {len(texts)}段文字, {len(tool_calls)}次工具调用")
        if texts:
            preview = texts[0][:80].replace("\n", " ")
            print(f"       回复预览: {preview}...")

        # memory check
        r = self.client.get("/api/v1/agent/memory", headers=self.auth("alice"))
        if r.status_code == 200:
            stats = r.json()["stats"]
            ok(f"AI记忆: 总消息={stats['total_messages']}, 用户={stats['user_messages']}")

    def check_db(self):
        try:
            from sqlalchemy import create_engine, text
            from app.config import settings

            engine = create_engine(settings.database_url)
            with engine.connect() as conn:
                db_type = "PostgreSQL" if "postgresql" in settings.database_url else "SQLite"
                ok(f"数据库类型: {db_type}")

                users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                clubs = conn.execute(text("SELECT COUNT(*) FROM clubs")).scalar()
                comps = conn.execute(text("SELECT COUNT(*) FROM competitions")).scalar()
                matches = conn.execute(text(
                    "SELECT COUNT(*) FROM matches WHERE score_a IS NOT NULL"
                )).scalar()
                convs = conn.execute(text("SELECT COUNT(*) FROM agent_conversations")).scalar()

                ok(f"users={users}, clubs={clubs}, competitions={comps}, scored_matches={matches}, agent_msgs={convs}")

                if users < 3:
                    self.errors.append(f"users表记录不足: {users}")
                if clubs < 1:
                    self.errors.append("clubs表无数据")
                if comps < 1:
                    self.errors.append("competitions表无数据")
                if matches < 1:
                    self.errors.append("matches无已录入比分")

                # 验证测试俱乐部存在
                row = conn.execute(text(
                    "SELECT id, name FROM clubs WHERE id = :id"
                ), {"id": self.club_id}).fetchone()
                if row:
                    ok(f"俱乐部数据: id={row[0]}, name={row[1]}")
                else:
                    self.errors.append("测试俱乐部在DB中不存在")

        except Exception as e:
            self.errors.append(f"DB check: {e}")


if __name__ == "__main__":
    sys.path.insert(0, ".")
    t0 = time.time()
    exit_code = LiveTest().run()
    print(f"\n耗时: {time.time() - t0:.1f}s")
    sys.exit(exit_code)
