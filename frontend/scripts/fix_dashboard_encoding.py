# -*- coding: utf-8 -*-
"""Rewrite Dashboard.tsx with correct UTF-8 Chinese (ASCII-only script)."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "pages" / "Dashboard.tsx"

# fmt: off
S = {
    "create_fail": "\u521b\u5efa\u5931\u8d25",
    "signup_fail": "\u62a5\u540d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5",
    "leave_fail": "\u9000\u8d5b\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5",
    "nailong": "\u5976\u9f99",
    "ai_q1": "\u4e0d\u77e5\u9053\u600e\u4e48\u505a\uff1f\u70b9\u51fb\u53f3\u4e0a\u89d2",
    "ai_btn": "\u300cAI \u52a9\u624b\u300d",
    "ai_q2": "\u95ee\u5976\u9f99\uff01",
    "ai_hint": "\u8bd5\u8bd5\u8bf4\uff1a\u300c\u5e2e\u6211\u521b\u5efa\u4e00\u4e2a\u516b\u4eba\u8f6c\u6bd4\u8d5b\u300d\u300c\u6211\u60f3\u52a0\u5165\u4ff1\u4e50\u90e8\u300d\u300c\u8bb0\u5f55\u6bd4\u5206 21:15\u300d",
    "my_clubs": "\U0001f3df\ufe0f \u6211\u7684\u4ff1\u4e50\u90e8",
    "club_ph": "\u8f93\u5165\u4ff1\u4e50\u90e8\u540d\u79f0",
    "create": "+ \u521b\u5efa",
    "loading": "\u52a0\u8f7d\u4e2d...",
    "no_club": "\u8fd8\u6ca1\u6709\u4ff1\u4e50\u90e8",
    "no_club_hint": "\u521b\u5efa\u4e00\u4e2a\u6216\u5728\u4e0b\u65b9\u641c\u7d22\u52a0\u5165",
    "club_icon": "\U0001f3df\ufe0f",
    "owner": "\u521b\u5efa\u8005",
    "members": "\u540d\u6210\u5458",
    "feat_loading": "\u52a0\u8f7d\u63a8\u8350...",
    "feat_title": "\U0001f525 \u70ed\u95e8\u4ff1\u4e50\u90e8\u63a8\u8350",
    "feat_hint": "\u4e0d\u77e5\u9053\u52a0\u5165\u54ea\u4e2a\uff1f\u770b\u770b\u5927\u5bb6\u90fd\u5728\u73a9\u4ec0\u4e48\uff1a",
    "unknown": "\u672a\u77e5",
    "joining": "\u52a0\u5165\u4e2d...",
    "join": "\u52a0\u5165",
    "search_club": "\U0001f50d \u52a0\u5165\u4ff1\u4e50\u90e8",
    "search_ph": "\u641c\u7d22\u4ff1\u4e50\u90e8\u540d\u79f0...",
    "searching": "\u641c\u7d22\u4e2d...",
    "joined": "\u5df2\u52a0\u5165",
    "no_match": "\u672a\u627e\u5230\u5339\u914d\u7684\u4ff1\u4e50\u90e8",
    "lobby": "\U0001f3f8 \u6bd4\u8d5b\u5927\u5385\uff08\u62a5\u540d\u4e2d\uff09",
    "comp_ph": "\u641c\u7d22\u6bd4\u8d5b\u540d\u6216\u521b\u5efa\u8005...",
    "search": "\u641c\u7d22",
    "signed": "\u5df2\u62a5\u540d",
    "public": "\u516c\u5f00\u62a5\u540d",
    "members_only": "\u4ec5\u4ff1\u4e50\u90e8\u6210\u5458",
    "creator": "\u521b\u5efa\u8005\uff1a",
    "deadline": "\u622a\u6b62\uff1a",
    "signing": "\u62a5\u540d\u4e2d...",
    "leaving": "\u9000\u8d5b\u4e2d...",
    "leave": "\u9000\u8d5b",
    "signed_btn": "\u5df2\u62a5\u540d",
    "closed": "\u5df2\u622a\u6b62",
    "full": "\u5df2\u6ee1\u5458",
    "signup": "\u62a5\u540d",
    "no_comp": "\u6682\u65e0\u62a5\u540d\u4e2d\u7684\u6bd4\u8d5b",
    "trophy": "\U0001f3c6",
    "create_lobby": "+ \u521b\u5efa\u5927\u5385\u6bd4\u8d5b",
    "mid": "\u00b7",
}
# fmt: on

CONTENT = f'''import {{ useEffect, useState }} from "react";
import {{ Link }} from "react-router-dom";
import type {{ Club, ClubSearchResult, CompetitionSummary }} from "../types";
import * as clubsApi from "../api/clubs";
import * as compApi from "../api/competitions";

export default function Dashboard() {{
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

  const loadClubs = () => {{
    setLoading(true);
    clubsApi.listClubs().then(setClubs).finally(() => setLoading(false));
  }};

  useEffect(() => {{
    loadClubs();
  }}, []);

  useEffect(() => {{
    setFeaturedLoading(true);
    clubsApi.searchClubs("")
      .then(results => {{
        const items = results.slice(0, 6).map(r => ({{
          id: r.id,
          name: r.name,
          owner_id: 0,
          owner_name: r.owner_name,
          member_count: r.member_count,
        }}));
        setFeaturedClubs(items);
      }})
      .catch(() => setFeaturedClubs([]))
      .finally(() => setFeaturedLoading(false));
  }}, []);

  const loadOpenCompetitions = async (q = "") => {{
    setCompLoading(true);
    try {{
      const data = await compApi.listOpenCompetitions(q);
      setOpenCompetitions(data);
    }} finally {{
      setCompLoading(false);
    }}
  }};

  useEffect(() => {{
    loadOpenCompetitions();
  }}, []);

  const handleCreate = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!newName.trim()) return;
    setError("");
    try {{
      await clubsApi.createClub(newName);
      setNewName("");
      loadClubs();
    }} catch (err: any) {{
      setError(err.response?.data?.detail || "{S["create_fail"]}");
    }}
  }};

  const handleSearch = async (q: string) => {{
    setSearchQ(q);
    if (!q.trim()) {{
      setSearchResults([]);
      return;
    }}
    setSearching(true);
    try {{
      const results = await clubsApi.searchClubs(q);
      setSearchResults(results);
    }} finally {{
      setSearching(false);
    }}
  }};

  const handleJoin = async (clubId: number) => {{
    setJoiningId(clubId);
    try {{
      await clubsApi.joinClub(clubId);
      loadClubs();
      setSearchResults(prev =>
        prev.map(c => (c.id === clubId ? {{ ...c, is_joined: true }} : c))
      );
      setFeaturedClubs(prev => prev.filter(c => c.id !== clubId));
    }} catch {{
      // silently fail - user can retry
    }} finally {{
      setJoiningId(null);
    }}
  }};

  const handleJoinCompetition = async (competitionId: number) => {{
    setJoiningCompId(competitionId);
    setCompError("");
    try {{
      await compApi.joinCompetition(competitionId);
      await loadOpenCompetitions(compSearchQ);
    }} catch (err: any) {{
      setCompError(err?.response?.data?.detail || "{S["signup_fail"]}");
    }} finally {{
      setJoiningCompId(null);
    }}
  }};

  const handleLeaveCompetition = async (competitionId: number) => {{
    setLeavingCompId(competitionId);
    setCompError("");
    try {{
      await compApi.leaveCompetition(competitionId);
      await loadOpenCompetitions(compSearchQ);
    }} catch (err: any) {{
      setCompError(err.response?.data?.detail || "{S["leave_fail"]}");
    }} finally {{
      setLeavingCompId(null);
    }}
  }};

  const isCompFull = (c: CompetitionSummary) =>
    c.max_players !== null && c.player_count >= c.max_players;

  const isCompDeadlinePassed = (c: CompetitionSummary) =>
    !!c.signup_deadline && new Date(c.signup_deadline).getTime() < Date.now();

  return (
    <div className="space-y-8">
      <div className="bg-gradient-to-r from-nailong-orange/10 to-nailong-yellow/10 border border-nailong-orange/20 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <img
          src="https://www.nailoong.com/img/ipStar/image_nailoong.png"
          alt="{S["nailong"]}"
          className="w-12 h-12 object-contain animate-nailong-swing shrink-0"
        />
        <div className="flex-1">
          <p className="text-gray-800 font-medium">
            {S["ai_q1"]}{{" "}}
            <span className="text-nailong-orange font-bold">{S["ai_btn"]}</span> {S["ai_q2"]}
          </p>
          <p className="text-gray-500 text-sm mt-0.5">
            {S["ai_hint"]}
          </p>
        </div>
      </div>

      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          {S["my_clubs"]}
        </h2>
        <form onSubmit={{handleCreate}} className="flex gap-3">
          <input
            value={{newName}}
            onChange={{e => setNewName(e.target.value)}}
            placeholder="{S["club_ph"]}"
            className="input-nailong flex-1"
            required
          />
          <button type="submit" className="btn-nailong whitespace-nowrap">
            {S["create"]}
          </button>
        </form>
        {{error && <p className="text-red-400 text-sm mt-3">{{error}}</p>}}
      </div>

      {{loading ? (
        <div className="text-center text-gray-400 py-12">{S["loading"]}</div>
      ) : clubs.length === 0 ? (
        <div className="text-center py-12 card-nailong">
          <img
            src="https://www.nailoong.com/img/ipStar/image_nailoong.png"
            alt="{S["nailong"]}"
            className="w-24 h-24 mx-auto mb-4 animate-nailong-bounce-gentle object-contain"
          />
          <p className="text-gray-500 text-lg font-medium">{S["no_club"]}</p>
          <p className="text-nailong-orange text-sm mt-1">{S["no_club_hint"]}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {{clubs.map(club => (
            <Link key={{club.id}} to={{`/clubs/${{club.id}}`}} className="card-nailong p-6 group">
              <div className="text-4xl mb-3 animate-nailong-float">{S["club_icon"]}</div>
              <h2 className="text-lg font-semibold text-gray-800 group-hover:text-nailong-orange transition">
                {{club.name}}
              </h2>
              <p className="text-gray-400 text-sm mt-1">
                {{club.owner_name ? `{S["owner"]}: ${{club.owner_name}}` : ""}}
                {{club.member_count !== undefined ? ` {S["mid"]} ${{club.member_count}} {S["members"]}` : ""}}
              </p>
            </Link>
          ))}}
        </div>
      )}}

      {{featuredLoading ? (
        <div className="text-center text-gray-400 py-6">{S["feat_loading"]}</div>
      ) : featuredClubs.length > 0 ? (
        <div className="card-nailong p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            {S["feat_title"]}
          </h2>
          <p className="text-gray-500 text-sm mb-4">{S["feat_hint"]}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {{featuredClubs.map(club => (
              <div
                key={{club.id}}
                className="flex items-center justify-between p-4 rounded-2xl bg-nailong-cream border border-nailong-cream-dark hover:border-nailong-orange/30 transition"
              >
                <div>
                  <div className="font-medium text-gray-800">{S["club_icon"]} {{club.name}}</div>
                  <div className="text-sm text-gray-400 mt-0.5">
                    {S["owner"]}: {{club.owner_name || "{S["unknown"]}"}} {S["mid"]} {{club.member_count || 0}} {S["members"]}
                  </div>
                </div>
                <button
                  onClick={{() => handleJoin(club.id)}}
                  disabled={{joiningId === club.id}}
                  className="btn-nailong text-sm disabled:opacity-50 whitespace-nowrap"
                >
                  {{joiningId === club.id ? "{S["joining"]}" : "{S["join"]}"}}
                </button>
              </div>
            ))}}
          </div>
        </div>
      ) : null}}

      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          {S["search_club"]}
        </h2>
        <input
          value={{searchQ}}
          onChange={{e => handleSearch(e.target.value)}}
          placeholder="{S["search_ph"]}"
          className="input-nailong mb-4"
        />

        {{searching ? (
          <div className="text-center text-gray-400 py-6">{S["searching"]}</div>
        ) : searchResults.length > 0 ? (
          <div className="space-y-3">
            {{searchResults.map(c => (
              <div
                key={{c.id}}
                className="flex items-center justify-between p-4 rounded-2xl bg-nailong-cream border border-nailong-cream-dark"
              >
                <div>
                  <div className="font-medium text-gray-800">{S["club_icon"]} {{c.name}}</div>
                  <div className="text-sm text-gray-400 mt-0.5">
                    {S["owner"]}: {{c.owner_name}} {S["mid"]} {{c.member_count}} {S["members"]}
                  </div>
                </div>
                {{c.is_joined ? (
                  <span className="text-sm text-gray-400 font-medium px-4 py-2">{S["joined"]}</span>
                ) : (
                  <button
                    onClick={{() => handleJoin(c.id)}}
                    disabled={{joiningId === c.id}}
                    className="btn-nailong text-sm disabled:opacity-50"
                  >
                    {{joiningId === c.id ? "{S["joining"]}" : "{S["join"]}"}}
                  </button>
                )}}
              </div>
            ))}}
          </div>
        ) : searchQ.trim() ? (
          <div className="text-center text-gray-400 py-6">{S["no_match"]}</div>
        ) : null}}
      </div>

      <div className="card-nailong p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            {S["lobby"]}
          </h2>
          <Link to="/create-lobby-competition" className="btn-nailong text-sm whitespace-nowrap text-center">
            {S["create_lobby"]}
          </Link>
        </div>
        <div className="flex gap-2 mb-4">
          <input
            value={{compSearchQ}}
            onChange={{e => setCompSearchQ(e.target.value)}}
            placeholder="{S["comp_ph"]}"
            className="input-nailong"
          />
          <button
            onClick={{() => loadOpenCompetitions(compSearchQ)}}
            className="btn-nailong-outline text-sm whitespace-nowrap"
          >
            {S["search"]}
          </button>
        </div>
        {{compError && <div className="text-sm text-red-500 mb-3">{{compError}}</div>}}

        {{compLoading ? (
          <div className="text-center text-gray-400 py-6">{S["loading"]}</div>
        ) : openCompetitions.length > 0 ? (
          <div className="space-y-3">
            {{openCompetitions.map(c => (
              <div
                key={{c.id}}
                className="flex items-center justify-between p-4 rounded-2xl bg-nailong-cream border border-nailong-cream-dark"
              >
                <div>
                  <Link
                    to={{`/competitions/${{c.id}}`}}
                    className="font-medium text-gray-800 hover:text-nailong-orange transition"
                  >
                    {S["trophy"]} {{c.name}}
                  </Link>
                  <div className="text-sm text-gray-500 mt-1">
                    {S["signed"]} {{c.player_count}}
                    {{c.max_players ? ` / ${{c.max_players}}` : ""}} {S["mid"]}{{" "}}
                    {{c.is_public ? "{S["public"]}" : "{S["members_only"]}"}}
                  </div>
                  {{c.creator_name && (
                    <div className="text-xs text-gray-400 mt-1">{S["creator"]}{{c.creator_name}}</div>
                  )}}
                  {{c.signup_deadline && (
                    <div className="text-xs text-gray-400 mt-1">
                      {S["deadline"]}{{new Date(c.signup_deadline).toLocaleString("zh-CN")}}
                    </div>
                  )}}
                </div>
                <button
                  onClick={{() =>
                    c.my_joined ? handleLeaveCompetition(c.id) : handleJoinCompetition(c.id)
                  }}
                  disabled={{
                    leavingCompId === c.id ||
                    joiningCompId === c.id ||
                    (!c.my_joined && (isCompFull(c) || isCompDeadlinePassed(c)))
                  }}
                  className={{c.my_joined
                      ? "btn-nailong-outline text-sm disabled:opacity-50"
                      : "btn-nailong text-sm disabled:opacity-50"
                  }}
                >
                  {{leavingCompId === c.id
                    ? "{S["leaving"]}"
                    : joiningCompId === c.id
                      ? "{S["signing"]}"
                      : c.my_joined
                        ? "{S["leave"]}"
                        : isCompDeadlinePassed(c)
                          ? "{S["closed"]}"
                          : isCompFull(c)
                            ? "{S["full"]}"
                            : "{S["signup"]}"}}
                </button>
              </div>
            ))}}
          </div>
        ) : (
          <div className="text-center text-gray-400 py-6">{S["no_comp"]}</div>
        )}}
      </div>
    </div>
  );
}}
'''

OUT.write_text(CONTENT, encoding="utf-8")
print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
