import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { CompetitionFormat } from "../types";
import { FORMAT_LABELS, FORMAT_PLAYER_COUNTS } from "../types";
import * as compApi from "../api/competitions";

export default function CreateLobbyCompetition() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [format, setFormat] = useState<CompetitionFormat>("eight_player_rotation");
  const [courts, setCourts] = useState(2);
  const [maxPlayers, setMaxPlayers] = useState("8");
  const [signupDeadline, setSignupDeadline] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const validCounts = FORMAT_PLAYER_COUNTS[format];
  const countLabel = validCounts.join("/");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const n = Number(maxPlayers);
    if (!validCounts.includes(n)) {
      setError(`当前赛制报名人数需为 ${countLabel}，你设置了 ${n} 人`);
      return;
    }
    setSubmitting(true);
    try {
      const comp = await compApi.createCompetition({
        name: name || `${FORMAT_LABELS[format]}（大厅）`,
        club_id: null,
        format,
        courts,
        player_ids: [],
        open_signup: true,
        is_public: true,
        max_players: n,
        signup_deadline: signupDeadline ? new Date(signupDeadline).toISOString() : undefined,
      });
      navigate(`/competitions/${comp.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/" className="text-nailong-orange text-sm hover:text-nailong-orange-dark font-medium">&larr; 返回首页</Link>
      <h1 className="text-2xl font-bold text-gray-800">创建大厅比赛</h1>
      <p className="text-gray-500 text-sm">公开报名，任何人可在比赛大厅加入，无需加入俱乐部。</p>
      <form onSubmit={handleSubmit} className="card-nailong p-6 space-y-5">
        {error && <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">比赛名称</label>
          <input value={name} onChange={e => setName(e.target.value)}
            placeholder="例：周八八人转"
            className="input-nailong w-full" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">赛制</label>
          <select value={format} onChange={e => setFormat(e.target.value as CompetitionFormat)}
            className="input-nailong w-full">
            {Object.entries(FORMAT_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">场地数</label>
            <input type="number" min={1} max={4} value={courts}
              onChange={e => setCourts(Number(e.target.value))}
              className="input-nailong w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">报名人数上限 ({countLabel})</label>
            <input type="number" value={maxPlayers}
              onChange={e => setMaxPlayers(e.target.value)}
              className="input-nailong w-full" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">报名截止时间（可选）</label>
          <input type="datetime-local" value={signupDeadline}
            onChange={e => setSignupDeadline(e.target.value)}
            className="input-nailong w-full" />
        </div>
        <button type="submit" disabled={submitting}
          className="btn-nailong w-full disabled:opacity-50">
          {submitting ? "创建中..." : "发布到大厅"}
        </button>
      </form>
    </div>
  );
}
