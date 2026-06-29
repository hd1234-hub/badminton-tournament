import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { Activity, CompetitionSummary } from "../types";
import * as clubsApi from "../api/clubs";
import * as compApi from "../api/competitions";
import * as activitiesApi from "../api/activities";

type Tab = "members" | "activities" | "competitions";

export default function ClubPage() {
  const { id } = useParams<{ id: string }>();
  const clubId = Number(id);
  const [players, setPlayers] = useState<any[]>([]);
  const [competitions, setCompetitions] = useState<CompetitionSummary[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("members");

  useEffect(() => {
    clubsApi.getClubPlayers(clubId).then(setPlayers).finally(() => setLoading(false));
  }, [clubId]);

  useEffect(() => {
    if (tab === "competitions") {
      compApi.listClubCompetitions(clubId).then(setCompetitions);
    }
    if (tab === "activities") {
      activitiesApi.listClubActivities(clubId).then(setActivities);
    }
  }, [clubId, tab]);

  const statusBadge = (status: string) => {
    const map: Record<string, { label: string; cls: string }> = {
      pending: { label: "待开始", cls: "bg-nailong-cream text-nailong-orange" },
      open: { label: "报名中", cls: "bg-green-100 text-green-700" },
      scheduled: { label: "已排期", cls: "bg-blue-100 text-blue-700" },
      completed: { label: "已结束", cls: "bg-gray-100 text-gray-500" },
    };
    const s = map[status] || { label: status, cls: "bg-gray-100 text-gray-500" };
    return <span className={`px-3 py-1 rounded-capsule text-xs font-medium ${s.cls}`}>{s.label}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center gap-3">
        <div>
          <Link to="/" className="text-nailong-orange text-sm hover:text-nailong-orange-dark mb-1 block font-medium">
            &larr; 返回首页
          </Link>
          <h1 className="text-2xl font-bold text-gray-800">俱乐部</h1>
        </div>
        <div className="flex gap-2">
          <Link to={`/clubs/${clubId}/dashboard`} className="px-4 py-2 rounded-capsule bg-white text-nailong-orange border border-nailong-orange text-sm font-medium">数据看板</Link>
          <Link to={`/clubs/${clubId}/create-activity`} className="btn-nailong text-sm">+ 发起活动</Link>
          <Link to={`/clubs/${clubId}/create-competition`} className="btn-nailong text-sm">+ 创建比赛</Link>
        </div>
      </div>

      <div className="flex gap-1 bg-white rounded-2xl p-1 shadow-nailong border border-nailong-cream-dark">
        {(["members", "activities", "competitions"] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-3 rounded-2xl font-medium text-sm transition ${
              tab === t ? "bg-nailong-orange text-white shadow-nailong" : "text-gray-500 hover:text-nailong-orange"
            }`}
          >
            {t === "members" ? `成员 (${players.length})` : t === "activities" ? `活动 (${activities.length})` : `比赛 (${competitions.length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-12">加载中...</div>
      ) : tab === "members" ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {players.map(p => (
            <div key={p.id} className="card-nailong p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-nailong-cream rounded-full flex items-center justify-center text-nailong-orange font-bold">{p.name[0]}</div>
                <div>
                  <div className="font-medium text-gray-800">{p.name}</div>
                  <div className="text-sm text-gray-400">{p.handedness === "right" ? "右手" : "左手"} · {p.gender === "male" ? "男" : "女"}</div>
                </div>
              </div>
              <span className="badge-nailong">Lv.{p.level}</span>
            </div>
          ))}
          {players.length === 0 && <div className="col-span-3 text-center py-12 text-gray-400">还没有成员</div>}
        </div>
      ) : tab === "activities" ? (
        <div className="space-y-3">
          {activities.map(activity => (
            <Link key={activity.id} to={`/activities/${activity.id}`} className="card-nailong p-5 flex items-center justify-between">
              <div>
                <div className="font-semibold text-gray-800">{activity.title}</div>
                <div className="text-sm text-gray-400 mt-1">{activity.confirmed_count}/{activity.max_players} · 候补 {activity.waitlist_count}</div>
              </div>
              {statusBadge(activity.status)}
            </Link>
          ))}
          {activities.length === 0 && <div className="text-center py-12 text-gray-400">还没有活动</div>}
        </div>
      ) : (
        <div className="space-y-3">
          {competitions.map(c => (
            <Link key={c.id} to={`/competitions/${c.id}`} className="card-nailong p-5 flex items-center justify-between group">
              <div className="flex items-center gap-4">
                <div className="text-2xl">🏆</div>
                <div>
                  <div className="font-semibold text-gray-800 group-hover:text-nailong-orange transition">{c.name}</div>
                  <div className="text-sm text-gray-400 mt-0.5">{c.player_count} 人 · {new Date(c.created_at).toLocaleDateString("zh-CN")}</div>
                </div>
              </div>
              {statusBadge(c.status)}
            </Link>
          ))}
          {competitions.length === 0 && <div className="text-center py-12 text-gray-400">还没有比赛</div>}
        </div>
      )}
    </div>
  );
}
