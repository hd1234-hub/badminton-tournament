#!/usr/bin/env python3
"""AI multi-round chain calling tests."""

import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"
USERNAME = "alice_0d9929b4"
PASSWORD = "test123456"


def parse_sse(body: str) -> list[dict]:
    events = []
    for line in body.split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


def chat(client: httpx.Client, token: str, message: str, timeout: float = 90.0) -> list[dict]:
    r = client.post(
        "/api/v1/agent/chat",
        json={"message": message, "history": []},
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
    )
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    return parse_sse(r.text)


def summarize(name: str, events: list[dict]) -> dict:
    tools = [e for e in events if e.get("type") == "tool_call"]
    texts = [e.get("content", "") for e in events if e.get("type") == "text"]
    navs = [e for e in events if e.get("type") == "nav_link"]
    errors = [e for e in events if e.get("type") == "error"]
    done = [e for e in events if e.get("type") == "done"]
    rounds = done[0].get("total_tool_rounds", "?") if done else "?"

    print(f"\n--- {name} ---")
    print(f"  events: start={'start' in [e.get('type') for e in events]}")
    print(f"  tool_calls: {len(tools)} -> {[t.get('name') for t in tools]}")
    print(f"  nav_links: {len(navs)}")
    print(f"  text_parts: {len(texts)}")
    print(f"  total_tool_rounds: {rounds}")
    if errors:
        print(f"  ERROR: {errors[0].get('content', '')[:120]}")
    if texts:
        preview = texts[-1][:100].replace("\n", " ")
        print(f"  reply: {preview}...")

    return {
        "name": name,
        "ok": not errors and "done" in [e.get("type") for e in events],
        "tools": [t.get("name") for t in tools],
        "rounds": rounds,
        "error": errors[0].get("content") if errors else None,
    }


def main():
    client = httpx.Client(base_url=BASE, timeout=120.0)
    results = []

    # login
    r = client.post("/api/v1/auth/login", json={"username": USERNAME, "password": PASSWORD})
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return 1
    token = r.json()["token"]
    print(f"Logged in as {USERNAME}")

    scenarios = [
        (
            "Test1: duel + score chain",
            "帮我跟鲍勃单挑，打完比分21比0",
        ),
        (
            "Test2: explicit create + score",
            "创建我和卡罗尔的单挑比赛，比分录入21:15",
        ),
        (
            "Test3: leaderboard query",
            "帮我看看俱乐部排行榜",
        ),
        (
            "Test4: view competition",
            "帮我看看比赛1的情况",
        ),
    ]

    for name, msg in scenarios:
        t0 = time.time()
        try:
            events = chat(client, token, msg)
            res = summarize(name, events)
            res["elapsed"] = round(time.time() - t0, 1)
            print(f"  elapsed: {res['elapsed']}s")
            results.append(res)
        except Exception as e:
            print(f"\n--- {name} ---")
            print(f"  FAILED: {e}")
            results.append({"name": name, "ok": False, "tools": [], "error": str(e)})
        time.sleep(2)  # avoid rate limit

    # DB verification
    print("\n=== DB Verification ===")
    from sqlalchemy import create_engine, text
    from app.config import settings

    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        comps = conn.execute(text(
            "SELECT id, name, status FROM competitions ORDER BY id DESC LIMIT 5"
        )).fetchall()
        print("  recent competitions:")
        for c in comps:
            print(f"    id={c[0]} name={c[1]} status={c[2]}")

        scored = conn.execute(text(
            "SELECT m.id, m.score_a, m.score_b, c.name FROM matches m "
            "JOIN rounds r ON m.round_id=r.id "
            "JOIN competitions c ON r.competition_id=c.id "
            "WHERE m.score_a IS NOT NULL ORDER BY m.id DESC LIMIT 5"
        )).fetchall()
        print("  recent scored matches:")
        for m in scored:
            print(f"    match#{m[0]} {m[3]} -> {m[1]}:{m[2]}")

        agent_count = conn.execute(text(
            "SELECT COUNT(*) FROM agent_conversations WHERE role='user'"
        )).scalar()
        print(f"  agent user messages total: {agent_count}")

    print("\n=== Summary ===")
    passed = sum(1 for r in results if r.get("ok"))
    for r in results:
        status = "PASS" if r.get("ok") else "FAIL"
        tools = " -> ".join(r.get("tools") or [])
        print(f"  [{status}] {r['name']}")
        if tools:
            print(f"         tools: {tools}")
        if r.get("error"):
            print(f"         error: {r['error'][:80]}")

  # Chain test expectations
    t1 = next((r for r in results if "Test1" in r["name"]), {})
    t2 = next((r for r in results if "Test2" in r["name"]), {})
    chain_ok = (
        "create_competition" in (t1.get("tools") or [])
        and "record_score" in (t1.get("tools") or [])
    ) or (
        "create_competition" in (t2.get("tools") or [])
        and "record_score" in (t2.get("tools") or [])
    )
    print(f"\n  Multi-round chain (create+score): {'PASS' if chain_ok else 'NEEDS REVIEW'}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.path.insert(0, ".")
    sys.exit(main())
