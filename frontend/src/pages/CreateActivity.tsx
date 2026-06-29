import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { CompetitionFormat } from "../types";
import { FORMAT_LABELS, FORMAT_PLAYER_COUNTS } from "../types";
import * as activitiesApi from "../api/activities";

export default function CreateActivity() {
  const { id } = useParams<{ id: string }>();
  const clubId = Number(id);
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [format, setFormat] = useState<CompetitionFormat>("eight_player_rotation");
  const [courts, setCourts] = useState(2);
  const [playerCount, setPlayerCount] = useState(8);
  const [startTime, setStartTime] = useState("");
  const [signupDeadline, setSignupDeadline] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setPlayerCount(FORMAT_PLAYER_COUNTS[format][0]);
  }, [format]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const activity = await activitiesApi.createActivity({
        title,
        club_id: clubId,
        format,
        courts,
        min_players: playerCount,
        max_players: playerCount,
        start_time: new Date(startTime).toISOString(),
        signup_deadline: new Date(signupDeadline).toISOString(),
        location: location || undefined,
        description: description || undefined,
      });
      navigate(`/activities/${activity.id}`);
    } catch (e: any) {
      setError(e.response?.data?.detail || "创建失败");
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <Link to={`/clubs/${clubId}`} className="text-nailong-orange text-sm hover:text-nailong-orange-dark mb-1 block font-medium">
          &larr; 返回俱乐部
        </Link>
        <h1 className="text-2xl font-bold text-gray-800">发起活动</h1>
      </div>

      <form onSubmit={submit} className="card-nailong p-6 space-y-4">
        {error && <div className="bg-red-50 text-red-500 rounded-2xl px-4 py-3 text-sm">{error}</div>}
        <input className="input-nailong" value={title} onChange={e => setTitle(e.target.value)} placeholder="活动标题" required />
        <input className="input-nailong" value={location} onChange={e => setLocation(e.target.value)} placeholder="地点" />
        <textarea className="input-nailong min-h-[96px]" value={description} onChange={e => setDescription(e.target.value)} placeholder="活动说明" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="text-sm text-gray-500 space-y-1">
            <span>赛制</span>
            <select className="input-nailong" value={format} onChange={e => setFormat(e.target.value as CompetitionFormat)}>
              {Object.entries(FORMAT_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="text-sm text-gray-500 space-y-1">
            <span>人数</span>
            <select className="input-nailong" value={playerCount} onChange={e => setPlayerCount(Number(e.target.value))}>
              {FORMAT_PLAYER_COUNTS[format].map(count => <option key={count} value={count}>{count} 人</option>)}
            </select>
          </label>
          <label className="text-sm text-gray-500 space-y-1">
            <span>场地数</span>
            <input className="input-nailong" type="number" min={1} max={4} value={courts} onChange={e => setCourts(Number(e.target.value))} />
          </label>
          <label className="text-sm text-gray-500 space-y-1">
            <span>开始时间</span>
            <input className="input-nailong" type="datetime-local" value={startTime} onChange={e => setStartTime(e.target.value)} required />
          </label>
          <label className="text-sm text-gray-500 space-y-1 md:col-span-2">
            <span>报名截止</span>
            <input className="input-nailong" type="datetime-local" value={signupDeadline} onChange={e => setSignupDeadline(e.target.value)} required />
          </label>
        </div>
        <button className="btn-nailong w-full" type="submit">创建活动</button>
      </form>
    </div>
  );
}
