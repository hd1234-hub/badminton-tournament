#!/usr/bin/env python3
"""Lightweight load test for open-signup competition flow."""

from __future__ import annotations

import asyncio
import os
import statistics
import time
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy import func, text

from app.database import SessionLocal
from app.models.player import Player
from app.models.user import User
from app.services.auth_service import create_token, hash_password

BASE_URL = os.getenv("LOAD_TEST_BASE_URL", "http://127.0.0.1:8001")
OWNER_USERNAME = os.getenv("LOAD_TEST_OWNER_USERNAME", "alice_0d9929b4")
OWNER_PASSWORD = os.getenv("LOAD_TEST_OWNER_PASSWORD", "test123456")
CLUB_ID = int(os.getenv("LOAD_TEST_CLUB_ID", "3"))
VIRTUAL_USERS = int(os.getenv("LOAD_TEST_USERS", "24"))
MAX_PLAYERS = int(os.getenv("LOAD_TEST_MAX_PLAYERS", "8"))
FORMAT = os.getenv("LOAD_TEST_FORMAT", "knockout")
SEARCH_REQUESTS = int(os.getenv("LOAD_TEST_SEARCH_REQUESTS", "80"))
SEARCH_CONCURRENCY = int(os.getenv("LOAD_TEST_SEARCH_CONCURRENCY", "12"))


@dataclass
class JoinResult:
    status: int
    elapsed_ms: float
    detail: str


def _create_virtual_user_tokens(n: int, suffix: str) -> list[str]:
    tokens: list[str] = []
    db = SessionLocal()
    try:
        max_user_id = db.query(func.max(User.id)).scalar() or 0
        max_player_id = db.query(func.max(Player.id)).scalar() or 0
        next_id = max(max_user_id, max_player_id) + 1
        for i in range(n):
            username = f"load_u_{suffix}_{i:03d}"
            name = f"压测{i:03d}"
            uid = next_id + i
            user = User(
                id=uid,
                username=username,
                hashed_password=hash_password("test123456"),
                name=name,
                gender="male",
                skill_level=3,
                birth_year=1995,
                bio="load test user",
            )
            db.add(user)
            db.flush()

            # 保证 user.id 对应 player 记录存在，便于 join 接口直接报名。
            db.add(Player(id=uid, name=name, gender="male", level=3))
            db.flush()

            tokens.append(create_token(uid))
        # 同步序列，避免后续常规注册/建球员冲突
        db.execute(text(
            "SELECT setval(pg_get_serial_sequence('users', 'id'), "
            "COALESCE((SELECT MAX(id) FROM users), 1))"
        ))
        db.execute(text(
            "SELECT setval(pg_get_serial_sequence('players', 'id'), "
            "COALESCE((SELECT MAX(id) FROM players), 1))"
        ))
        db.commit()
        return tokens
    finally:
        db.close()


async def _join_once(client: httpx.AsyncClient, comp_id: int, token: str) -> JoinResult:
    headers = {"Authorization": f"Bearer {token}"}
    t0 = time.perf_counter()
    resp = await client.post(f"/api/v1/competitions/{comp_id}/join", headers=headers)
    elapsed = (time.perf_counter() - t0) * 1000
    detail = ""
    try:
        payload = resp.json()
        if isinstance(payload, dict):
            detail = str(payload.get("detail", ""))
    except Exception:
        detail = resp.text[:120]
    return JoinResult(status=resp.status_code, elapsed_ms=elapsed, detail=detail)


async def _search_once(client: httpx.AsyncClient, token: str, q: str) -> float:
    headers = {"Authorization": f"Bearer {token}"}
    t0 = time.perf_counter()
    resp = await client.get("/api/v1/competitions/open", params={"q": q}, headers=headers)
    resp.raise_for_status()
    return (time.perf_counter() - t0) * 1000


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    idx = min(len(values_sorted) - 1, max(0, int(round((p / 100) * (len(values_sorted) - 1)))))
    return values_sorted[idx]


async def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    print(f"BASE_URL={BASE_URL}")
    print(f"Creating {VIRTUAL_USERS} virtual users...")
    tokens = _create_virtual_user_tokens(VIRTUAL_USERS, suffix)

    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=timeout, trust_env=False) as client:
        owner_login = await client.post(
            "/api/v1/auth/login",
            json={"username": OWNER_USERNAME, "password": OWNER_PASSWORD},
        )
        if owner_login.status_code != 200:
            print(f"[FAIL] Owner login failed: {owner_login.status_code} {owner_login.text[:200]}")
            return 1
        owner_token = owner_login.json()["token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        comp_name = f"压测报名_{suffix}"
        create_resp = await client.post(
            "/api/v1/competitions",
            headers=owner_headers,
            json={
                "name": comp_name,
                "club_id": CLUB_ID,
                "format": FORMAT,
                "courts": 2,
                "player_ids": [],
                "open_signup": True,
                "is_public": True,
                "max_players": MAX_PLAYERS,
            },
        )
        if create_resp.status_code != 200:
            print(f"[FAIL] Create competition failed: {create_resp.status_code} {create_resp.text[:200]}")
            return 1
        comp = create_resp.json()
        comp_id = comp["id"]
        print(f"[OK] Created open competition id={comp_id}, current players={len(comp['players'])}")

        print("\n=== Concurrent join pressure ===")
        join_tasks = [_join_once(client, comp_id, t) for t in tokens]
        join_results = await asyncio.gather(*join_tasks)
        latencies = [r.elapsed_ms for r in join_results]

        success = [r for r in join_results if r.status == 200]
        full = [r for r in join_results if r.status == 400 and "已满" in r.detail]
        busy = [r for r in join_results if r.status == 400 and "拥挤" in r.detail]
        other_4xx = [r for r in join_results if 400 <= r.status < 500 and r not in full and r not in busy]
        server_err = [r for r in join_results if r.status >= 500]

        print(
            f"join total={len(join_results)} success={len(success)} "
            f"full={len(full)} busy={len(busy)} other4xx={len(other_4xx)} 5xx={len(server_err)}"
        )
        print(
            f"join latency(ms): avg={statistics.mean(latencies):.1f} "
            f"p50={_pct(latencies,50):.1f} p95={_pct(latencies,95):.1f} max={max(latencies):.1f}"
        )

        comp_after = await client.get(f"/api/v1/competitions/{comp_id}", headers=owner_headers)
        comp_after.raise_for_status()
        players_count = len(comp_after.json()["players"])
        print(f"players after join={players_count} (expected <= {MAX_PLAYERS})")

        print("\n=== Open lobby search pressure ===")
        sem = asyncio.Semaphore(SEARCH_CONCURRENCY)

        async def _search_guarded() -> float:
            async with sem:
                return await _search_once(client, owner_token, "压测")

        search_latencies = await asyncio.gather(*[_search_guarded() for _ in range(SEARCH_REQUESTS)])
        print(
            f"search requests={len(search_latencies)} "
            f"avg={statistics.mean(search_latencies):.1f}ms "
            f"p50={_pct(search_latencies,50):.1f}ms "
            f"p95={_pct(search_latencies,95):.1f}ms "
            f"max={max(search_latencies):.1f}ms"
        )

        if players_count > MAX_PLAYERS or server_err:
            print("[FAIL] Data consistency or server stability check failed.")
            return 1

        print("\n[PASS] Load test completed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

