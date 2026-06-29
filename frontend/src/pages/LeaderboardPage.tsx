import { useEffect, useState } from "react";
import type { Club } from "../types";
import type { LeaderboardEntry } from "../api/leaderboard";
import * as clubsApi from "../api/clubs";
import * as lbApi from "../api/leaderboard";

const PAGE_SIZE = 20;

type Tab = "global" | number;

function rankBadge(rank: number) {
  if (rank === 1) return "bg-yellow-400 text-white";
  if (rank === 2) return "bg-gray-300 text-white";
  if (rank === 3) return "bg-orange-300 text-white";
  return "bg-gray-100 text-gray-500";
}

export default function LeaderboardPage() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("global");
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => { clubsApi.listClubs().then(setClubs); }, []);

  useEffect(() => {
    setSkip(0);
    if (activeTab === "global") {
      lbApi.getGlobalLeaderboard(0, PAGE_SIZE).then(res => {
        setEntries(res.entries);
        setTotal(res.total);
      });
    } else {
      lbApi.getLeaderboard(activeTab, 0, PAGE_SIZE).then(res => {
        setEntries(res.entries);
        setTotal(res.total);
      });
    }
  }, [activeTab]);

  const loadMore = async () => {
    setLoadingMore(true);
    const nextSkip = skip + PAGE_SIZE;
    let res;
    if (activeTab === "global") {
      res = await lbApi.getGlobalLeaderboard(nextSkip, PAGE_SIZE);
    } else {
      res = await lbApi.getLeaderboard(activeTab, nextSkip, PAGE_SIZE);
    }
    setEntries(prev => [...prev, ...res.entries]);
    setSkip(nextSkip);
    setLoadingMore(false);
  };

  const hasMore = entries.length < total;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="relative overflow-hidden card-nailong p-6 bg-gradient-to-br from-nailong-cream via-white to-yellow-50">
        <div className="absolute right-4 top-2 opacity-95 pointer-events-none">
          <img
            src="https://www.nailoong.com/img/ipStar/image_nailoong.png"
            alt="奶龙"
            className="w-28 h-28 object-contain animate-nailong-float"
          />
        </div>
        <div className="relative pr-28">
          <p className="badge-nailong inline-flex mb-3">冠军榜</p>
          <h1 className="text-3xl font-extrabold text-gray-800">排行榜</h1>
          <p className="text-sm text-gray-500 mt-2">奶龙正在盯榜，看看今天谁是球场冠军。</p>
        </div>
      </div>
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setActiveTab("global")}
          className={"px-4 py-2 rounded-[30px] font-medium transition " + (activeTab === "global" ? "btn-nailong shadow-nailong" : "bg-white text-gray-600 border-2 border-nailong-cream-dark hover:border-nailong-yellow")}>
          全部排行
        </button>
        {clubs.map(c => (
          <button key={c.id} onClick={() => setActiveTab(c.id)}
            className={"px-4 py-2 rounded-[30px] font-medium transition " + (activeTab === c.id ? "btn-nailong shadow-nailong" : "bg-white text-gray-600 border-2 border-nailong-cream-dark hover:border-nailong-yellow")}>
            {c.name}
          </button>
        ))}
      </div>

      {entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((e, i) => (
            <div key={e.id} className="card-nailong p-4 flex items-center gap-4 hover:shadow-nailong-lg transition">
              {/* Rank */}
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${rankBadge(i + 1)}`}>
                {i + 1}
              </div>

              {/* Player info */}
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-800 truncate">{e.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  总局 {e.total_matches} · 胜率 {(e.win_rate * 100).toFixed(0)}%
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center gap-4 text-sm shrink-0">
                <div className="text-center">
                  <div className="text-green-600 font-bold">{e.wins}</div>
                  <div className="text-[10px] text-gray-400">胜</div>
                </div>
                <div className="text-center">
                  <div className="text-red-400 font-bold">{e.losses}</div>
                  <div className="text-[10px] text-gray-400">负</div>
                </div>
                <div className="text-center min-w-[3rem]">
                  <div className={`font-bold ${e.point_diff > 0 ? "text-nailong-orange" : e.point_diff < 0 ? "text-gray-400" : "text-gray-500"}`}>
                    {e.point_diff > 0 ? "+" : ""}{e.point_diff}
                  </div>
                  <div className="text-[10px] text-gray-400">净胜</div>
                </div>
              </div>
            </div>
          ))}

          {hasMore && (
            <div className="p-4 text-center">
              <button onClick={loadMore} disabled={loadingMore}
                      className="btn-nailong text-sm">
                {loadingMore ? "加载中..." : `加载更多 (${total - entries.length} 条剩余)`}
              </button>
            </div>
          )}
        </div>
      )}

      {entries.length === 0 && (
        <div className="text-center py-12 text-gray-400">暂无排名数据</div>
      )}
    </div>
  );
}
