#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix Dashboard layout and encoding - put lobby first, remove top nav lobby link"""

import os
import re

DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "pages", "Dashboard.tsx")
LAYOUT_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "components", "Layout.tsx")

def fix_layout():
    """Remove lobby link from top navigation"""
    with open(LAYOUT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove the lobby link from top nav
    content = re.sub(
        r'\s*<Link to="/create-lobby-competition"[^>]*>大厅</Link>\s*',
        "",
        content
    )
    
    with open(LAYOUT_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] Layout: removed lobby from top nav")

def fix_dashboard():
    """Regenerate Dashboard with lobby section first"""
    
    dashboard_code = r'''import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Club, ClubSearchResult, CompetitionSummary } from "../types";
import * as clubsApi from "../api/clubs";
import * as compApi from "../api/competitions";

export default function Dashboard() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(true);
  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState<ClubSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [joiningId, setJoiningId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [openCompetitions, setOpenCompetitions] = useState<CompetitionSummary[]>([]);
  const [compSearchQ, setCompSearchQ] = useState("");
  const [joiningCompId, setJoiningCompId] = useState<number | null>(null);
  const [leavingCompId, setLeavingCompId] = useState<number | null>(null);
  const [compLoading, setCompLoading] = useState(false);
  const [compError, setCompError] = useState("");
  const [featuredClubs, setFeaturedClubs] = useState<Club[]>([]);
  const [featuredLoading, setFeaturedLoading] = useState(true);

  const loadClubs = () => {
    setLoading(true);
    clubsApi.listClubs().then(setClubs).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadClubs();
  }, []);

  useEffect(() => {
    setFeaturedLoading(true);
    clubsApi.searchClubs("")
      .then(results => {
        const items = results.slice(0, 6).map(r => ({
          id: r.id,
          name: r.name,
          owner_id: 0,
          owner_name: r.owner_name,
          member_count: r.member_count,
        }));
        setFeaturedClubs(items);
      })
      .catch(() => setFeaturedClubs([]))
      .finally(() => setFeaturedLoading(false));
  }, []);

  const loadOpenCompetitions = async (q = "") => {
    setCompLoading(true);
    try {
      const data = await compApi.listOpenCompetitions(q);
      setOpenCompetitions(data);
    } finally {
      setCompLoading(false);
    }
  };

  useEffect(() => {
    loadOpenCompetitions();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setError("");
    try {
      await clubsApi.createClub(newName);
      setNewName("");
      loadClubs();
    } catch (err: any) {
      setError(err.response?.data?.detail || "创建失败");
    }
  };

  const handleSearch = async (q: string) => {
    setSearchQ(q);
    if (!q.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const results = await clubsApi.searchClubs(q);
      setSearchResults(results);
    } finally {
      setSearching(false);
    }
  };

  const handleJoin = async (clubId: number) => {
    setJoiningId(clubId);
    try {
      await clubsApi.joinClub(clubId);
      loadClubs();
      setSearchResults(prev =>
        prev.map(c => (c.id === clubId ? { ...c, is_joined: true } : c))
      );
      setFeaturedClubs(prev => prev.filter(c => c.id !== clubId));
    } catch {
      // silently fail - user can retry
    } finally {
      setJoiningId(null);
    }
  };

  const handleJoinCompetition = async (competitionId: number) => {
    setJoiningCompId(competitionId);
    setCompError("");
    try {
      await compApi.joinCompetition(competitionId);
      await loadOpenCompetitions(compSearchQ);
    } catch (err: any) {
      setCompError(err?.response?.data?.detail || "报名失败，请稍后重试");
    } finally {
      setJoiningCompId(null);
    }
  };

  const handleLeaveCompetition = async (competitionId: number) => {
    setLeavingCompId(competitionId);
    setCompError("");
    try {
      await compApi.leaveCompetition(competitionId);
      await loadOpenCompetitions(compSearchQ);
    } catch (err: any) {
      setCompError(err.response?.data?.detail || "退赛失败，请稍后重试");
    } finally {
      setLeavingCompId(null);
    }
  };

  const isCompFull = (c: CompetitionSummary) =>
    c.max_players !== null && c.player_count >= c.max_players;

  const isCompDeadlinePassed = (c: CompetitionSummary) =>
    !!c.signup_deadline && new Date(c.signup_deadline).getTime() < Date.now();

  const scrollToCompetitions = () => {
    const el = document.getElementById('open-competitions');
    el?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="space-y-8">
      {/* 欢迎语 */}
      <div className="bg-gradient-to-r from-nailong-orange/10 to-nailong-yellow/10 border border-nailong-orange/20 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <img
          src="https://www.nailoong.com/img/ipStar/image_nailoong.png"
          alt="奶龙"
          className="w-12 h-12 object-contain animate-nailong-swing shrink-0"
        />
        <div className="flex-1">
          <p className="text-gray-800 font-medium">
            不知道怎么做？点击右上角{" "}
            <span className="text-nailong-orange font-bold">「AI 助手」</span> 问奶龙！
          </p>
          <p className="text-gray-500 text-sm mt-0.5">
            试试说：「帮我创建一个八人转比赛」「我想加入俱乐部」「记录比分 21:15」
          </p>
        </div>
      </div>

      {/* 大厅入口 - 竖排第一个 */}
      <div className="card-nailong p-6 bg-gradient-to-r from-nailong-orange/5 to-nailong-yellow/5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="text-4xl shrink-0">🏆</div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">比赛大厅</h2>
            <p className="text-gray-500 text-sm">
              无需加入俱乐部，公开报名，快速开始一场羽毛球对决
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            <Link to="/create-lobby-competition" className="btn-nailong whitespace-nowrap">
              + 创建大厅比赛
            </Link>
            <button
              onClick={scrollToCompetitions}
              className="btn-nailong-outline whitespace-nowrap"
            >
              去报名 ↓
            </button>
          </div>
        </div>
      </div>

      {/* 我的俱乐部 */}
      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          🏟️ 我的俱乐部
        </h2>
        <form onSubmit={handleCreate} className="flex gap-3">
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="输入俱乐部名称"
            className="input-nailong flex-1"
            required
          />
          <button type="submit" className="btn-nailong whitespace-nowrap">
            + 创建
          </button>
        </form>
        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-12">加载中...</div>
      ) : clubs.length === 0 ? (
        <div className="text-center py-12 card-nailong">
          <img
            src="https://www.nailoong.com/img/ipStar/image_nailoong.png"
            alt="奶龙"
            className="w-24 h-24 mx-auto mb-4 animate-nailong-bounce-gentle object-contain"
          />
          <p className="text-gray-500 text-lg font-medium">还没有俱乐部</p>
          <p className="text-nailong-orange text-sm mt-1">创建一个或在下方搜索加入</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clubs.map(club => (
            <Link key={club.id} to={`/clubs/${club.id}`} className="card-nailong p-6 group">
              <div className="text-4xl mb-3 animate-nailong-float">🏟️</div>
              <h2 className="text-lg font-semibold text-gray-800 group-hover:text-nailong-orange transition">
                {club.name}
              </h2>
              <p className="text-gray-400 text-sm mt-1">
                {club.owner_name ? `创建者: ${club.owner_name}` : ""}
                {club.member_count !== undefined ? ` · ${club.member_count} 名成员` : ""}
              </p>
            </Link>
          ))}
        </div>
      )}

      {/* 热门俱乐部推荐 */}
      {featuredLoading ? (
        <div className="text-center text-gray-400 py-6">加载推荐...</div>
      ) : featuredClubs.length > 0 ? (
        <div className="card-nailong p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            🔥 热门俱乐部推荐
          </h2>
          <p className="text-gray-500 text-sm mb-4">不知道加入哪个？看看大家都在玩什么：</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredClubs.map(club => (
              <div
                key={club.id}
                className="flex items-center justify-between p-4 rounded-2xl bg-nailong-cream border border-nailong-cream-dark hover:border-nailong-orange/30 transition"
              >
                <div>
                  <div className="font-medium text-gray-800">📍 {club.name}</div>
                  <div className="text-sm text-gray-400 mt-0.5">
                    创建者: {club.owner_name || "未知"} · {club.member_count || 0} 名成员
                  </div>
                </div>
                <button
                  onClick={() => handleJoin(club.id)}
                  disabled={joiningId === club.id}
                  className="btn-nailong text-sm disabled:opacity-50 whitespace-nowrap"
                >
                  {joiningId === club.id ? "加入中..." : "加入"}
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* 搜索俱乐部 */}
      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          🔍 搜索俱乐部
        </h2>
        <input
          value={searchQ}
          onChange={e => handleSearch(e.target.value)}
          placeholder="输入俱乐部名称搜索..."
          className="input-nailong mb-4"
        />

        {searching ? (
          <div className="text-center text-gray-400 py-6">搜索中...</div>
        ) : searchResults.length > 0 ? (
          <div className="space-y-3">
            {searchResults.map(c => (
              <div
                key={c.id}
                className="flex items-center justify-between p-4 rounded-2xl bg-nailong-cream border border-nailong-cream-dark"
              >
                <div>
                  <div className="font-medium text-gray-800">📍 {c.name}</div>
                  <div className="text-sm text-gray-400 mt-0.5">
                    创建者: {c.owner_name} · {c.member_count} 名成员
                  </div>
                </div>
                {c.is_joined ? (
                  <span className="text-sm text-gray-400 font-medium px-4 py-2">已加入</span>
                ) : (
                  <button
                    onClick={() => handleJoin(c.id)}
                    disabled={joiningId === c.id}
                    className="btn-nailong text-sm disabled:opacity-50"
                  >
                    {joiningId === c.id ? "加入中..." : "加入"}
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : searchQ.trim() ? (
          <div className="text-center text-gray-400 py-6">没有找到匹配的俱乐部</div>
        ) : null}
      </div>

      {/* 正在报名 - 大厅比赛列表 */}
      <div id="open-competitions" className="card-nailong p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            🏆 正在报名
          </h2>
          <Link to="/create-lobby-competition" className="btn-nailong text-sm whitespace-nowrap text-center">
            + 创建比赛
          </Link>
        </div>
        <div className="flex gap-2 mb-4">
          <input
            value={compSearchQ}
            onChange={e => setCompSearchQ(e.target.value)}
            placeholder="搜索比赛名或创建者..."
            className="input-nailong"
          />
          <button
            onClick={() => loadOpenCompetitions(compSearchQ)}
            className="btn-nailong-outline text-sm whitespace-nowrap"
          >
            搜索
          </button>
        </div>
        {compError && <div className="text-sm text-red-500 mb-3">{compError}</div>}

        {compLoading ? (
          <div className="text-center text-gray-400 py-6">加载中...</div>
        ) : openCompetitions.length > 0 ? (
          <div className="space-y-3">
            {openCompetitions.map(c => (
              <div
                key={c.id}
                className="flex items-center justify-between p-4 rounded-2xl bg-nailong-cream border border-nailong-cream-dark"
              >
                <div>
                  <Link
                    to={`/competitions/${c.id}`}
                    className="font-medium text-gray-800 hover:text-nailong-orange transition"
                  >
                    🏆 {c.name}
                  </Link>
                  <div className="text-sm text-gray-500 mt-1">
                    已报名 {c.player_count}
                    {c.max_players ? ` / ${c.max_players}` : ""} ·{" "}
                    {c.is_public ? "公开报名" : "仅俱乐部成员"}
                  </div>
                  {c.creator_name && (
                    <div className="text-xs text-gray-400 mt-1">创建者：{c.creator_name}</div>
                  )}
                  {c.signup_deadline && (
                    <div className="text-xs text-gray-400 mt-1">
                      截止：{new Date(c.signup_deadline).toLocaleString("zh-CN")}
                    </div>
                  )}
                </div>
                <button
                  onClick={() =>
                    c.my_joined ? handleLeaveCompetition(c.id) : handleJoinCompetition(c.id)
                  }
                  disabled={
                    leavingCompId === c.id ||
                    joiningCompId === c.id ||
                    (!c.my_joined && (isCompFull(c) || isCompDeadlinePassed(c)))
                  }
                  className={c.my_joined
                      ? "btn-nailong-outline text-sm disabled:opacity-50"
                      : "btn-nailong text-sm disabled:opacity-50"
                  }
                >
                  {leavingCompId === c.id
                    ? "退赛中..."
                    : joiningCompId === c.id
                      ? "报名中..."
                      : c.my_joined
                        ? "退赛"
                        : isCompDeadlinePassed(c)
                          ? "已截止"
                          : isCompFull(c)
                            ? "已满员"
                            : "报名"}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-400 py-6">暂无报名中的比赛</div>
        )}
      </div>
    </div>
  );
}
'''
    
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(dashboard_code)
    print("✅ Dashboard: regenerated with lobby section first")

if __name__ == "__main__":
    fix_layout()
    fix_dashboard()
    print("\\n🎉 Done! Dashboard layout fixed.")
