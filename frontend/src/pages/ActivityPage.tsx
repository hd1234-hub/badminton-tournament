import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Activity } from "../types";
import * as activitiesApi from "../api/activities";

export default function ActivityPage() {
  const { id } = useParams<{ id: string }>();
  const activityId = Number(id);
  const navigate = useNavigate();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    activitiesApi.getActivity(activityId).then(setActivity).catch(() => setError("活动加载失败")).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [activityId]);

  const run = async (action: () => Promise<any>) => {
    setError("");
    try {
      const result = await action();
      if (result?.id && result?.rounds) {
        navigate(`/competitions/${result.id}`);
      } else {
        setActivity(result);
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || "操作失败");
    }
  };

  if (loading) return <div className="text-center text-gray-400 py-12">加载中...</div>;
  if (!activity) return <div className="text-center text-gray-400 py-12">活动不存在</div>;

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/clubs/${activity.club_id}`} className="text-nailong-orange text-sm hover:text-nailong-orange-dark mb-1 block font-medium">
          &larr; 返回俱乐部
        </Link>
        <h1 className="text-2xl font-bold text-gray-800">{activity.title}</h1>
        <p className="text-gray-500 mt-1">{new Date(activity.start_time).toLocaleString("zh-CN")}</p>
      </div>

      {error && <div className="bg-red-50 text-red-500 rounded-2xl px-4 py-3 text-sm">{error}</div>}

      <div className="card-nailong p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
          <div className="bg-nailong-cream rounded-2xl p-4">
            <div className="text-xl font-bold text-nailong-orange">{activity.confirmed_count}/{activity.max_players}</div>
            <div className="text-xs text-gray-500 mt-1">确认报名</div>
          </div>
          <div className="bg-nailong-cream rounded-2xl p-4">
            <div className="text-xl font-bold text-nailong-orange">{activity.waitlist_count}</div>
            <div className="text-xs text-gray-500 mt-1">候补</div>
          </div>
          <div className="bg-nailong-cream rounded-2xl p-4">
            <div className="text-xl font-bold text-nailong-orange">{activity.courts}</div>
            <div className="text-xs text-gray-500 mt-1">场地</div>
          </div>
          <div className="bg-nailong-cream rounded-2xl p-4">
            <div className="text-xl font-bold text-nailong-orange">{activity.status === "open" ? "报名中" : "已排期"}</div>
            <div className="text-xs text-gray-500 mt-1">状态</div>
          </div>
        </div>

        <div className="text-sm text-gray-500 space-y-1">
          {activity.location && <p>地点：{activity.location}</p>}
          <p>报名截止：{new Date(activity.signup_deadline).toLocaleString("zh-CN")}</p>
          {activity.description && <p>{activity.description}</p>}
        </div>

        <div className="flex flex-wrap gap-2">
          {activity.my_signup_status ? (
            <button onClick={() => run(() => activitiesApi.cancelSignup(activity.id))} className="px-4 py-2 rounded-capsule bg-gray-100 text-gray-600 text-sm font-medium">
              取消报名
            </button>
          ) : (
            <button onClick={() => run(() => activitiesApi.signup(activity.id))} className="btn-nailong text-sm">
              报名
            </button>
          )}
          <button onClick={() => run(() => activitiesApi.generateCompetition(activity.id))} className="btn-nailong text-sm">
            生成比赛
          </button>
          {activity.competition_id && <Link to={`/competitions/${activity.competition_id}`} className="px-4 py-2 rounded-capsule bg-green-100 text-green-700 text-sm font-medium">进入比赛</Link>}
        </div>
      </div>

      <div className="card-nailong p-6">
        <h2 className="font-semibold text-gray-800 mb-4">报名名单</h2>
        <div className="space-y-2">
          {activity.signups.map(s => (
            <div key={s.id} className="flex items-center justify-between rounded-2xl bg-nailong-cream px-4 py-3">
              <span className="font-medium text-gray-700">{s.player.name}</span>
              <span className="text-xs text-gray-500">{s.status === "confirmed" ? "确认" : "候补"}</span>
            </div>
          ))}
          {activity.signups.length === 0 && <div className="text-center text-gray-400 py-8">暂无报名</div>}
        </div>
      </div>
    </div>
  );
}
