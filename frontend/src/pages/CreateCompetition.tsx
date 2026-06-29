import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import type { Player, CompetitionFormat } from "../types";
import { FORMAT_LABELS, FORMAT_PLAYER_COUNTS } from "../types";
import * as clubsApi from "../api/clubs";
import * as compApi from "../api/competitions";

export default function CreateCompetition() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [players, setPlayers] = useState<Player[]>([]);
  const [name, setName] = useState("");
  const [format, setFormat] = useState<CompetitionFormat>("eight_player_rotation");
  const [courts, setCourts] = useState(2);
  const [selected, setSelected] = useState<number[]>([]);
  const [scheduledAt, setScheduledAt] = useState<string>("");
  const [openSignup, setOpenSignup] = useState(false);
  const [isPublic, setIsPublic] = useState(true);
  const [maxPlayers, setMaxPlayers] = useState<string>("");
  const [signupDeadline, setSignupDeadline] = useState<string>("");
  const [error, setError] = useState("");

  useEffect(() => {
    clubsApi.getClubPlayers(Number(id)).then(setPlayers);
  }, [id]);

  const togglePlayer = (pid: number) => {
    setSelected(prev => prev.includes(pid) ? prev.filter(p => p !== pid) : [...prev, pid]);
  };

  const validCounts = FORMAT_PLAYER_COUNTS[format];
  const isValidPlayerCount = validCounts.includes(selected.length);
  const minPlayers = Math.min(...validCounts);
  const maxPlayerCount = Math.max(...validCounts);
  const countLabel = validCounts.length > 3
    ? `${minPlayers}-${maxPlayerCount}人`
    : validCounts.join("/");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!openSignup && !isValidPlayerCount) {
      setError(`当前赛制需要 ${countLabel}，已选 ${selected.length} 人`);
      return;
    }
    if (openSignup && maxPlayers) {
      const n = Number(maxPlayers);
      if (!validCounts.includes(n)) {
        setError(`当前赛制报名人数上限需为 ${countLabel}，你设置了 ${n} 人`);
        return;
      }
    }
    try {
      const comp = await compApi.createCompetition({
        name: name || `${FORMAT_LABELS[format]}`,
        club_id: Number(id),
        format,
        courts,
        player_ids: openSignup ? [] : selected,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : undefined,
        open_signup: openSignup,
        is_public: openSignup ? isPublic : false,
        max_players: openSignup && maxPlayers ? Number(maxPlayers) : undefined,
        signup_deadline: openSignup && signupDeadline ? new Date(signupDeadline).toISOString() : undefined,
      });
      navigate("/competitions/" + comp.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || "创建失败");
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to={"/clubs/" + id} className="text-nailong-orange text-sm hover:text-nailong-orange-dark font-medium">&larr; 返回俱乐部</Link>
      <h1 className="text-2xl font-bold text-gray-800">创建比赛</h1>
      <form onSubmit={handleSubmit} className="card-nailong p-6 space-y-5">
        {error && <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">比赛名称</label>
          <input value={name} onChange={e => setName(e.target.value)}
                 className="input-nailong" placeholder={`例如：周日下午${FORMAT_LABELS[format]}`} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">比赛格式</label>
            <select value={format} onChange={e => { setFormat(e.target.value as CompetitionFormat); setSelected([]); }}
                    className="input-nailong bg-white">
              {Object.entries(FORMAT_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">场地数</label>
            <select value={courts} onChange={e => setCourts(Number(e.target.value))}
                    className="input-nailong bg-white">
              <option value={1}>1 场地</option>
              <option value={2}>2 场地</option>
              <option value={4}>4 场地</option>
            </select>
          </div>
        </div>
        <div className="bg-nailong-cream border border-nailong-cream-dark rounded-2xl p-4 space-y-3">
          <label className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">开放自主报名</span>
            <input
              type="checkbox"
              checked={openSignup}
              onChange={(e) => setOpenSignup(e.target.checked)}
              className="accent-nailong-orange w-4 h-4"
            />
          </label>
          {openSignup && (
            <div className="space-y-3 pt-1">
              <label className="flex items-center justify-between">
                <span className="text-sm text-gray-600">大厅可见（非俱乐部也可报名）</span>
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="accent-nailong-orange w-4 h-4"
                />
              </label>
              <div>
                <label className="block text-sm text-gray-600 mb-2">报名人数上限（可选）</label>
                <input
                  type="number"
                  min={2}
                  max={64}
                  value={maxPlayers}
                  onChange={(e) => setMaxPlayers(e.target.value)}
                  className="input-nailong"
                  placeholder="例如 16"
                />
              </div>
              <p className="text-xs text-gray-500">当前赛制允许人数：{countLabel}</p>
              <div>
                <label className="block text-sm text-gray-600 mb-2">报名截止时间（可选）</label>
                <input
                  type="datetime-local"
                  value={signupDeadline}
                  onChange={(e) => setSignupDeadline(e.target.value)}
                  className="input-nailong"
                />
              </div>
              <p className="text-xs text-gray-500">创建后状态为“报名中”，你会自动报名。人数凑够后可进入比赛页点击“开始比赛”。</p>
            </div>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">比赛时间 <span className="text-gray-400 font-normal">（可选）</span></label>
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={e => setScheduledAt(e.target.value)}
            className="input-nailong"
          />
        </div>
        {!openSignup && (
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-3">
            选择球员
            <span className={`ml-2 badge-nailong text-xs font-bold ${isValidPlayerCount ? "" : "bg-red-100 text-red-600"}`}>
              {selected.length}/{countLabel}
            </span>
          </label>
          {players.length > 0 && players.length < minPlayers && (
            <div className="bg-nailong-cream border border-nailong-yellow text-nailong-orange p-4 rounded-2xl text-sm mb-3">
              俱乐部仅有 {players.length} 名成员，需要至少 {minPlayers} 人才能创建{FORMAT_LABELS[format]}
            </div>
          )}
          <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
            {players.map(p => (
              <button key={p.id} type="button" onClick={() => togglePlayer(p.id)}
                className={"p-3 rounded-2xl text-left transition border-2 " + (selected.includes(p.id) ? "bg-nailong-cream border-nailong-yellow shadow-nailong" : "border-nailong-cream-dark bg-white hover:border-nailong-yellow")}>
                <div className="flex items-center gap-2">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${selected.includes(p.id) ? "bg-nailong-orange text-white" : "bg-gray-200 text-gray-500"}`}>
                    {selected.includes(p.id) ? "V" : ""}
                  </span>
                  <span className="font-medium text-gray-800">{p.name}</span>
                  <span className="text-gray-400 text-xs ml-auto">Lv.{p.level}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
        )}
        <button type="submit" disabled={!openSignup && !isValidPlayerCount}
                className="btn-nailong w-full disabled:opacity-50 disabled:cursor-not-allowed">
          {openSignup ? "发布报名比赛" : "生成对阵表"}
        </button>
      </form>
    </div>
  );
}
