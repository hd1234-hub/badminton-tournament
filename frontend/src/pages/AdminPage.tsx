import { useEffect, useMemo, useState } from "react";
import * as adminApi from "../api/admin";
import type { AdminOverviewStats, AdminUserItem, AdminCompetitionItem } from "../api/admin";

const STATUS_LABELS: Record<string, string> = {
  pending: "待开始",
  in_progress: "进行中",
  completed: "已结束",
};

function StatCard({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="card-nailong p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-nailong-orange mt-2">{value}</p>
      {hint && <p className="text-xs text-gray-400 mt-2">{hint}</p>}
    </div>
  );
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminOverviewStats | null>(null);
  const [trend, setTrend] = useState<adminApi.RegistrationTrendItem[]>([]);
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [competitions, setCompetitions] = useState<AdminCompetitionItem[]>([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const pageSize = 15;
  const maxTrendCount = useMemo(() => Math.max(...trend.map(t => t.count), 1), [trend]);

  useEffect(() => {
    setLoading(true);
    setError("");
    Promise.all([
      adminApi.getAdminStats(),
      adminApi.getRegistrationTrend(30),
      adminApi.listAdminUsers(page, pageSize, search),
      adminApi.listRecentCompetitions(8),
    ])
      .then(([statsData, trendData, userData, competitionData]) => {
        setStats(statsData);
        setTrend(trendData);
        setUsers(userData.items);
        setTotalUsers(userData.total);
        setCompetitions(competitionData);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "加载运营数据失败");
      })
      .finally(() => setLoading(false));
  }, [page, search]);

  const totalPages = Math.max(1, Math.ceil(totalUsers / pageSize));

  if (loading && !stats) {
    return <div className="p-8 text-center text-gray-500">加载运营数据...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">运营后台</h1>
          <p className="text-sm text-gray-500 mt-1">用户注册、比赛与 AI 使用概览</p>
        </div>
        <button
          onClick={() => {
            setPage(1);
            setSearch(searchInput);
          }}
          className="btn-nailong-outline text-sm"
        >
          刷新
        </button>
      </div>

      {error && <div className="card-nailong p-4 text-red-500 text-sm">{error}</div>}

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="总注册用户" value={stats.total_users} />
          <StatCard label="今日新增" value={stats.today_registrations} hint={`近7日 ${stats.week_registrations} 人`} />
          <StatCard label="7日活跃(AI)" value={stats.active_users_7d} hint="近7日有 AI 对话的用户" />
          <StatCard label="俱乐部数" value={stats.total_clubs} />
          <StatCard label="比赛总数" value={stats.total_competitions} hint={`进行中 ${stats.competitions_in_progress}`} />
          <StatCard label="已完成比赛" value={stats.completed_competitions} />
          <StatCard label="AI 消息总数" value={stats.agent_messages_total} hint={`今日 ${stats.agent_messages_today}`} />
          <StatCard label="今日 AI 消息" value={stats.agent_messages_today} />
        </div>
      )}

      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">近 30 日注册趋势</h2>
        <div className="flex items-end gap-1 h-40 overflow-x-auto pb-2">
          {trend.map(item => (
            <div key={item.date} className="flex flex-col items-center min-w-[18px] flex-1">
              <span className="text-[10px] text-gray-400 mb-1">{item.count || ""}</span>
              <div
                className="w-full max-w-[24px] rounded-t-lg bg-nailong-orange/80 transition-all"
                style={{ height: `${Math.max((item.count / maxTrendCount) * 120, item.count ? 8 : 2)}px` }}
                title={`${item.date}: ${item.count} 人`}
              />
              <span className="text-[9px] text-gray-400 mt-2 rotate-[-45deg] origin-top-left whitespace-nowrap">
                {item.date.slice(5)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="card-nailong p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
          <h2 className="text-lg font-semibold text-gray-800">用户列表</h2>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setPage(1);
              setSearch(searchInput.trim());
            }}
          >
            <input
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              placeholder="搜索用户名或昵称"
              className="input-nailong w-56"
            />
            <button type="submit" className="btn-nailong-outline text-sm">搜索</button>
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-nailong-cream-dark">
                <th className="py-2 pr-4">ID</th>
                <th className="py-2 pr-4">用户名</th>
                <th className="py-2 pr-4">昵称</th>
                <th className="py-2 pr-4">注册时间</th>
                <th className="py-2 pr-4">俱乐部</th>
                <th className="py-2 pr-4">AI 消息</th>
                <th className="py-2">角色</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id} className="border-b border-nailong-cream-dark last:border-0">
                  <td className="py-3 pr-4 text-gray-500">{user.id}</td>
                  <td className="py-3 pr-4 font-medium text-gray-800">{user.username}</td>
                  <td className="py-3 pr-4">{user.name}</td>
                  <td className="py-3 pr-4 text-gray-500">{formatDate(user.created_at)}</td>
                  <td className="py-3 pr-4">{user.club_count}</td>
                  <td className="py-3 pr-4">{user.agent_messages}</td>
                  <td className="py-3">
                    {user.is_admin ? (
                      <span className="px-2 py-0.5 rounded-full bg-nailong-orange/15 text-nailong-orange text-xs">管理员</span>
                    ) : (
                      <span className="text-gray-400 text-xs">普通用户</span>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-400">暂无用户</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
          <span>共 {totalUsers} 人</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className="btn-nailong-outline text-xs disabled:opacity-40"
            >
              上一页
            </button>
            <span>{page} / {totalPages}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
              className="btn-nailong-outline text-xs disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">最近比赛</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-nailong-cream-dark">
                <th className="py-2 pr-4">ID</th>
                <th className="py-2 pr-4">名称</th>
                <th className="py-2 pr-4">俱乐部</th>
                <th className="py-2 pr-4">人数</th>
                <th className="py-2 pr-4">状态</th>
                <th className="py-2">创建时间</th>
              </tr>
            </thead>
            <tbody>
              {competitions.map(comp => (
                <tr key={comp.id} className="border-b border-nailong-cream-dark last:border-0">
                  <td className="py-3 pr-4 text-gray-500">{comp.id}</td>
                  <td className="py-3 pr-4 font-medium text-gray-800">{comp.name}</td>
                  <td className="py-3 pr-4">#{comp.club_id}</td>
                  <td className="py-3 pr-4">{comp.player_count}</td>
                  <td className="py-3 pr-4">{STATUS_LABELS[comp.status] || comp.status}</td>
                  <td className="py-3 text-gray-500">{formatDate(comp.created_at)}</td>
                </tr>
              ))}
              {competitions.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-400">暂无比赛</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
