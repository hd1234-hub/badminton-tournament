import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { MyCompetitionSummary } from "../types";
import * as competitionsApi from "../api/competitions";

const STATUS_LABEL: Record<string, string> = {
  open: "报名中",
  pending: "待开始",
  in_progress: "进行中",
  completed: "已结束",
};

export default function MyCompetitionsPage() {
  const [items, setItems] = useState<MyCompetitionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    competitionsApi.listMyCompetitions().then(setItems).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center text-gray-400 py-12">加载中...</div>;
  }

  const totalMatches = items.reduce((sum, item) => sum + item.my_matches, 0);
  const totalWins = items.reduce((sum, item) => sum + item.my_wins, 0);
  const totalLosses = items.reduce((sum, item) => sum + item.my_losses, 0);
  const totalWinRate = totalMatches > 0 ? (totalWins / totalMatches) * 100 : 0;

  return (
    <div className="space-y-6">
      <div className="card-nailong p-6">
        <h1 className="text-2xl font-bold text-gray-800">我的比赛</h1>
        <p className="text-sm text-gray-500 mt-2">已参赛 {items.length} 场 · 对局 {totalMatches} · 胜率 {totalWinRate.toFixed(0)}%</p>
        <p className="text-sm text-gray-500 mt-1">总战绩：{totalWins} 胜 {totalLosses} 负</p>
      </div>

      {items.length === 0 ? (
        <div className="card-nailong p-8 text-center text-gray-400">你还没有参与比赛</div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <Link key={item.id} to={`/competitions/${item.id}`} className="card-nailong p-5 flex items-center justify-between">
              <div>
                <div className="font-semibold text-gray-800">🏆 {item.name}</div>
                <div className="text-sm text-gray-500 mt-1">
                  状态：{STATUS_LABEL[item.status] || item.status} · 我的战绩 {item.my_wins} 胜 {item.my_losses} 负
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  对局 {item.my_matches} · 胜率 {(item.my_win_rate * 100).toFixed(0)}% · 创建于 {new Date(item.created_at).toLocaleDateString("zh-CN")}
                </div>
              </div>
              <span className="text-nailong-orange text-sm font-medium">查看详情</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

