import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { DashboardData } from "../types";
import * as dashboardApi from "../api/dashboard";

const pct = (v: number) => `${Math.round(v * 100)}%`;

export default function ClubDashboardPage() {
  const { id } = useParams<{ id: string }>();
  const clubId = Number(id);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getClubDashboard(clubId).then(setData).finally(() => setLoading(false));
  }, [clubId]);

  if (loading) return <div className="text-center text-gray-400 py-12">加载中...</div>;
  if (!data) return <div className="text-center text-gray-400 py-12">暂无数据</div>;

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/clubs/${clubId}`} className="text-nailong-orange text-sm hover:text-nailong-orange-dark mb-1 block font-medium">
          &larr; 返回俱乐部
        </Link>
        <h1 className="text-2xl font-bold text-gray-800">数据看板</h1>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-nailong p-5"><div className="text-2xl font-bold text-nailong-orange">{data.summary.matches}</div><div className="text-sm text-gray-500">参赛场次</div></div>
        <div className="card-nailong p-5"><div className="text-2xl font-bold text-nailong-orange">{pct(data.summary.win_rate)}</div><div className="text-sm text-gray-500">胜率</div></div>
        <div className="card-nailong p-5"><div className="text-2xl font-bold text-nailong-orange">{data.summary.wins}</div><div className="text-sm text-gray-500">胜场</div></div>
        <div className="card-nailong p-5"><div className="text-2xl font-bold text-nailong-orange">{data.summary.avg_score.toFixed(1)}</div><div className="text-sm text-gray-500">场均得分</div></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="card-nailong p-6">
          <h2 className="font-semibold text-gray-800 mb-4">最近 5 场趋势</h2>
          <div className="space-y-3">
            {data.recent_trend.map(item => (
              <div key={item.match_id} className="flex items-center justify-between rounded-2xl bg-nailong-cream px-4 py-3">
                <div>
                  <div className="font-medium text-gray-700">{item.competition_name}</div>
                  <div className="text-xs text-gray-400">第 {item.round_number} 轮 · {item.team_score}:{item.opponent_score}</div>
                </div>
                <span className={`text-sm font-semibold ${item.won ? "text-green-600" : "text-red-400"}`}>{item.won ? "胜" : "负"}</span>
              </div>
            ))}
            {data.recent_trend.length === 0 && <div className="text-center text-gray-400 py-8">暂无已录入比分</div>}
          </div>
        </section>

        <section className="card-nailong p-6">
          <h2 className="font-semibold text-gray-800 mb-4">胜率曲线</h2>
          <div className="space-y-3">
            {data.win_rate_curve.map((point, index) => (
              <div key={point.match_id} className="space-y-1">
                <div className="flex justify-between text-xs text-gray-500"><span>第 {index + 1} 场</span><span>{pct(point.win_rate)}</span></div>
                <div className="h-2 bg-nailong-cream rounded-full overflow-hidden"><div className="h-full bg-nailong-orange" style={{ width: pct(point.win_rate) }} /></div>
              </div>
            ))}
            {data.win_rate_curve.length === 0 && <div className="text-center text-gray-400 py-8">暂无曲线数据</div>}
          </div>
        </section>

        <section className="card-nailong p-6">
          <h2 className="font-semibold text-gray-800 mb-4">对阵关系图</h2>
          <div className="space-y-2">
            {data.opponent_relationships.slice(0, 8).map(item => (
              <div key={item.player_id} className="flex items-center justify-between rounded-2xl bg-nailong-cream px-4 py-3">
                <span className="font-medium text-gray-700">{item.player_name}</span>
                <span className="text-sm text-gray-500">{item.matches} 场 · {pct(item.win_rate)} · 净胜 {item.avg_point_diff.toFixed(1)}</span>
              </div>
            ))}
            {data.opponent_relationships.length === 0 && <div className="text-center text-gray-400 py-8">暂无对阵数据</div>}
          </div>
        </section>

        <section className="card-nailong p-6">
          <h2 className="font-semibold text-gray-800 mb-4">搭档胜率矩阵</h2>
          <div className="space-y-2">
            {data.partner_matrix.slice(0, 8).map(item => (
              <div key={`${item.player_a_id}-${item.player_b_id}`} className="flex items-center justify-between rounded-2xl bg-nailong-cream px-4 py-3">
                <span className="font-medium text-gray-700">{item.player_a_name} / {item.player_b_name}</span>
                <span className="text-sm text-gray-500">{item.matches} 场 · {pct(item.win_rate)}</span>
              </div>
            ))}
            {data.partner_matrix.length === 0 && <div className="text-center text-gray-400 py-8">暂无搭档数据</div>}
          </div>
        </section>
      </div>
    </div>
  );
}
