import { useParams, Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { useCompetition } from "../hooks/useCompetition";
import * as compApi from "../api/competitions";
import { useAuth } from "../hooks/useAuth";
import SurrenderCard from "../components/SurrenderCard";
import ShareCard from "../components/ShareCard";
import PredictionCard, { resolvePredictions } from "../components/PredictionCard";
import { isFinalScore, validateDirectScore, validateScorePair } from "../utils/scoring";

function playerGenderLabel(gender: string) {
  if (gender === "male" || gender === "男") return "男";
  if (gender === "female" || gender === "女") return "女";
  return gender || "未知";
}

function playerHandLabel(handedness: string) {
  if (handedness === "right" || handedness === "右手") return "右手";
  if (handedness === "left" || handedness === "左手") return "左手";
  return handedness || "未知";
}

export default function CompetitionBoard() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { comp, refresh } = useCompetition(Number(id));
  const [editing, setEditing] = useState<{ matchId: number; scoreA: string; scoreB: string } | null>(null);
  const [editError, setEditError] = useState("");
  const [scoreError, setScoreError] = useState<{ matchId: number; message: string } | null>(null);
  const [joinError, setJoinError] = useState("");
  const [leaving, setLeaving] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [surrender, setSurrender] = useState<{
    loserNames: string[]; winnerNames: string[]; scoreA: number; scoreB: number;
  } | null>(null);
  const [shareOpen, setShareOpen] = useState(false);
  const [predictionOpen, setPredictionOpen] = useState(false);
  const [predictionResults, setPredictionResults] = useState<Array<{
    matchId: number; predictionId: string; predictedWinner: string; actualWinner: string; verdict: "correct" | "wrong";
  }>>([]);

  // Resolve predictions when matches end
  useEffect(() => {
    if (!comp) return;
    const results: typeof predictionResults = [];
    for (const rnd of comp.rounds) {
      for (const m of rnd.matches) {
        if (m.score_a !== null && m.score_b !== null && isFinalScore(m.score_a, m.score_b)) {
          results.push(...resolvePredictions(m.id, m.team_a, m.team_b, m.score_a, m.score_b, getName));
        }
      }
    }
    if (results.length > 0) setPredictionResults(prev => [...prev, ...results]);
  }, [comp]);

  if (!comp) return <div className="text-center py-12 text-gray-400">加载中...</div>;

  const handleStart = async () => {
    await compApi.startCompetition(comp.id);
    refresh();
  };

  const handlePlusOne = async (matchId: number, side: "a" | "b") => {
    const match = findMatch(matchId);
    if (!match) return;
    const a = match.score_a ?? 0;
    const b = match.score_b ?? 0;
    if (isFinalScore(a, b)) return;

    let newA = a, newB = b;
    if (side === "a") newA++;
    else newB++;

    const err = validateScorePair(newA, newB);
    if (err) {
      setScoreError({ matchId, message: err });
      setTimeout(() => setScoreError(null), 3000);
      return;
    }

    try {
      await compApi.recordScore(matchId, newA, newB);
      setScoreError(null);
      refresh();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "计分失败，请重试";
      setScoreError({ matchId, message: msg });
      setTimeout(() => setScoreError(null), 3000);
    }
  };

  const handleMinusOne = async (matchId: number, side: "a" | "b") => {
    const match = findMatch(matchId);
    if (!match || match.score_a === null || match.score_b === null) return;
    let newA = match.score_a;
    let newB = match.score_b;
    if (side === "a" && newA > 0) newA--;
    else if (side === "b" && newB > 0) newB--;
    else return;
    try {
      await compApi.recordScore(matchId, newA, newB);
      setScoreError(null);
      refresh();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "计分失败，请重试";
      setScoreError({ matchId, message: msg });
      setTimeout(() => setScoreError(null), 3000);
    }
  };

  const handleEdit = async () => {
    if (!editing) return;
    const a = Number(editing.scoreA);
    const b = Number(editing.scoreB);
    if (isNaN(a) || isNaN(b)) { setEditError("请输入有效数字"); return; }

    const err = validateDirectScore(a, b);
    if (err) { setEditError(err); return; }

    try {
      await compApi.recordScore(editing.matchId, a, b);
      setEditing(null);
      setEditError("");
      refresh();
    } catch (err: any) {
      setEditError(err.response?.data?.detail || "修改失败");
    }
  };

  const handleFinish = async () => {
    try {
      await compApi.finishCompetition(comp.id);
      setFinishing(false);
      refresh();
    } catch { /* ignore */ }
  };

  const findMatch = (matchId: number) => {
    for (const rnd of comp.rounds)
      for (const m of rnd.matches)
        if (m.id === matchId) return m;
    return null;
  };

  const statusText: Record<string, string> = { open: "报名中", pending: "待开始", in_progress: "进行中", completed: "已结束" };
  const getName = (pid: number) => comp.players.find(p => p.id === pid)?.name ?? `球员${pid}`;
  const joined = !!user && comp.players.some((p) => p.id === user.id);
  const full = comp.max_players !== null && comp.players.length >= comp.max_players;
  const deadlinePassed = !!comp.signup_deadline && new Date(comp.signup_deadline).getTime() < Date.now();

  // 格式化比赛时间
  const formatScheduledTime = (isoString: string | null | undefined) => {
    if (!isoString) return null;
    const date = new Date(isoString);
    return date.toLocaleString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      weekday: "short",
    });
  };

  // 计算积分排名
  const standings = new Map<number, { name: string; wins: number; losses: number; pointDiff: number }>();
  comp.players.forEach(p => standings.set(p.id, { name: p.name, wins: 0, losses: 0, pointDiff: 0 }));
  for (const rnd of comp.rounds) {
    for (const m of rnd.matches) {
      if (m.score_a === null || m.score_b === null) continue;
      const aWon = m.score_a > m.score_b;
      const diff = m.score_a - m.score_b;
      for (const pid of m.team_a) {
        const s = standings.get(pid);
        if (s) {
          aWon ? s.wins++ : s.losses++;
          s.pointDiff += diff;
        }
      }
      for (const pid of m.team_b) {
        const s = standings.get(pid);
        if (s) {
          aWon ? s.losses++ : s.wins++;
          s.pointDiff -= diff;
        }
      }
    }
  }
  const ranked = [...standings.values()]
    .filter(s => s.wins + s.losses > 0)
    .sort((a, b) => b.wins - a.wins || b.pointDiff - a.pointDiff || a.losses - b.losses);

  return (
    <div className="space-y-6">
      <Link to="/" className="text-nailong-orange text-sm hover:text-nailong-orange-dark font-medium">&larr; 返回首页</Link>
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{comp.name}</h1>
          {comp.scheduled_at && (
            <div className="text-sm text-gray-500 mt-1 flex items-center gap-1">
              <span>📅</span>
              <span>{formatScheduledTime(comp.scheduled_at)}</span>
            </div>
          )}
        </div>
        <div className="flex gap-3 items-center">
          <span className="badge-nailong">{statusText[comp.status] || comp.status}</span>
          {comp.status === "open" && !joined && (
            <button
              onClick={async () => {
                setJoinError("");
                try {
                  await compApi.joinCompetition(comp.id);
                  refresh();
                } catch (err: any) {
                  setJoinError(err?.response?.data?.detail || "报名失败，请稍后重试");
                }
              }}
              disabled={full || deadlinePassed}
              className="btn-nailong-outline text-sm disabled:opacity-50"
            >
              {deadlinePassed ? "报名已截止" : full ? "报名已满" : "报名参加"}
            </button>
          )}
          {comp.status === "open" && joined && (
            <button
              onClick={async () => {
                setJoinError("");
                setLeaving(true);
                try {
                  await compApi.leaveCompetition(comp.id);
                  refresh();
                } catch (err: any) {
                  setJoinError(err?.response?.data?.detail || "退赛失败，请稍后重试");
                } finally {
                  setLeaving(false);
                }
              }}
              disabled={leaving}
              className="bg-red-50 text-red-600 border border-red-200 font-semibold py-2 px-4 rounded-[30px] text-sm hover:bg-red-100 transition disabled:opacity-50"
            >
              {leaving ? "退赛中..." : "退出报名"}
            </button>
          )}
          {comp.status === "pending" && (
            <button onClick={handleStart} className="btn-nailong text-sm">开始比赛</button>
          )}
          {comp.status === "open" && (
            <button onClick={handleStart} className="btn-nailong text-sm">开始比赛</button>
          )}
          {comp.status === "in_progress" && (
            <button onClick={() => setFinishing(true)} className="bg-red-400 text-white font-semibold py-2 px-4 rounded-[30px] text-sm hover:bg-red-500 transition">
              结束比赛
            </button>
          )}
          {comp.status !== "completed" && (
            <button onClick={() => setPredictionOpen(true)} className="text-sm px-3 py-1.5 rounded-[30px] bg-purple-100 text-purple-600 hover:bg-purple-200 transition font-medium">
              毒奶预测
            </button>
          )}
          {comp.status === "completed" && (
            <button onClick={() => setShareOpen(true)} className="btn-nailong text-sm">
              生成分享卡
            </button>
          )}
        </div>
      </div>

      {ranked.length > 0 && (
        <div className="card-nailong p-5">
          <h2 className="text-sm font-semibold text-gray-600 mb-4">当前排名</h2>
          <div className="space-y-3">
            {ranked.map((s, i) => (
              <div key={s.name} className={`flex items-center gap-4 rounded-2xl px-4 py-3 ${i === 0 ? "bg-yellow-50" : i === 1 ? "bg-gray-50" : i === 2 ? "bg-orange-50" : "bg-white border border-nailong-cream-dark"}`}>
                <span className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0 ${i === 0 ? "bg-yellow-500" : i === 1 ? "bg-gray-400" : i === 2 ? "bg-orange-400" : "bg-gray-300"}`}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-800 truncate">{s.name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">排名第 {i + 1}</div>
                </div>
                <div className="flex items-center gap-4 text-sm shrink-0">
                  <div className="text-center">
                    <div className="text-green-600 font-bold">{s.wins}</div>
                    <div className="text-[10px] text-gray-400">胜</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-400 font-bold">{s.losses}</div>
                    <div className="text-[10px] text-gray-400">负</div>
                  </div>
                  <div className="text-center min-w-[3rem]">
                    <div className={`font-bold ${s.pointDiff > 0 ? "text-nailong-orange" : s.pointDiff < 0 ? "text-gray-400" : "text-gray-500"}`}>
                      {s.pointDiff > 0 ? "+" : ""}{s.pointDiff}
                    </div>
                    <div className="text-[10px] text-gray-400">净胜分</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {comp.status === "open" && (
        <div className="card-nailong p-5">
          {joinError && <div className="text-sm text-red-500 mb-3">{joinError}</div>}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-gray-500 mb-4">
            <div>
              当前报名：
              <span className="font-semibold text-gray-800 ml-1">
                {comp.players.length}
                {comp.max_players ? ` / ${comp.max_players}` : ""}
              </span>
            </div>
            {comp.signup_deadline && (
              <div>
                截止：
                <span className="font-semibold text-gray-800 ml-1">
                  {new Date(comp.signup_deadline).toLocaleString("zh-CN")}
                </span>
              </div>
            )}
          </div>

          <h3 className="text-sm font-semibold text-gray-600 mb-3">报名名单</h3>
          <div className="space-y-3">
            {comp.players.map((p) => (
              <div
                key={p.id}
                className={`flex items-center gap-3 p-4 rounded-2xl border transition ${
                  user?.id === p.id
                    ? "bg-nailong-cream border-nailong-orange/30"
                    : "bg-white border-nailong-cream-dark"
                }`}
              >
                <div className="w-11 h-11 bg-nailong-cream rounded-full flex items-center justify-center text-nailong-orange font-bold shrink-0">
                  {p.name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-800 truncate">{p.name}</div>
                  <div className="text-sm text-gray-400 mt-0.5">
                    {playerGenderLabel(p.gender)} · {playerHandLabel(p.handedness)} · Lv.{p.level || 3}
                  </div>
                </div>
                {user?.id === p.id && (
                  <span className="text-xs font-medium text-nailong-orange shrink-0 px-2 py-1 rounded-full bg-nailong-orange/10">
                    我
                  </span>
                )}
              </div>
            ))}
            {comp.players.length === 0 && (
              <div className="text-center py-10 text-gray-400 text-sm border border-dashed border-nailong-cream-dark rounded-2xl">
                还没人报名，快来第一个加入吧
              </div>
            )}
          </div>
        </div>
      )}

      {comp.rounds.map(rnd => (
        <div key={rnd.id} className="card-nailong overflow-hidden">
          <h2 className="bg-gradient-to-r from-nailong-cream to-nailong-cream-dark px-5 py-3 font-semibold text-gray-700">
            第 {rnd.round_number} 轮
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2">
            {rnd.matches.map(m => {
              const scored = m.score_a !== null;
              const gameOver = scored && isFinalScore(m.score_a!, m.score_b!);
              const disabled = comp.status !== "in_progress" || gameOver;

              return (
                <div key={m.id} className="p-5 border-t md:border-t-0 md:border-l border-gray-100">
                  <div className="text-xs text-gray-400 mb-3 font-medium">场地 {m.court}</div>

                  {/* Score display */}
                  <div className="flex items-center justify-between">
                    {/* Team A */}
                    <div className="flex-1 text-center">
                      <div className="text-sm text-gray-500 mb-1">{m.team_a.map(getName).join(" / ")}</div>
                      <div className="relative inline-block">
                        <span className={`text-3xl font-bold font-mono ${gameOver && m.score_a! > m.score_b! ? "text-nailong-orange" : scored ? "text-gray-800" : "text-gray-300"}`}>
                          {m.score_a ?? "-"}
                        </span>
                        {scored && comp.status !== "pending" && (
                          <button onClick={() => setEditing({ matchId: m.id, scoreA: String(m.score_a), scoreB: String(m.score_b!) })}
                                  className="absolute -top-1 -right-5 text-gray-400 hover:text-nailong-orange text-xs" title="编辑比分">
                            &#9998;
                          </button>
                        )}
                      </div>
                    </div>

                    <span className="px-4 text-gray-300 font-bold text-lg">VS</span>

                    {/* Team B */}
                    <div className="flex-1 text-center">
                      <div className="text-sm text-gray-500 mb-1">{m.team_b.map(getName).join(" / ")}</div>
                      <div className="relative inline-block">
                        <span className={`text-3xl font-bold font-mono ${gameOver && m.score_b! > m.score_a! ? "text-nailong-orange" : scored ? "text-gray-800" : "text-gray-300"}`}>
                          {m.score_b ?? "-"}
                        </span>
                        {scored && comp.status !== "pending" && (
                          <button onClick={() => setEditing({ matchId: m.id, scoreA: String(m.score_a), scoreB: String(m.score_b!) })}
                                  className="absolute -top-1 -right-5 text-gray-400 hover:text-nailong-orange text-xs" title="编辑比分">
                            &#9998;
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {gameOver && (
                    <div className="mt-3 text-center text-sm font-medium text-nailong-orange">
                      本场结束 {m.score_a! > m.score_b! ? m.team_a.map(getName).join("/") : m.team_b.map(getName).join("/")} 获胜
                      <button
                        onClick={() => {
                          const aWon = m.score_a! > m.score_b!;
                          setSurrender({
                            loserNames: (aWon ? m.team_b : m.team_a).map(getName),
                            winnerNames: (aWon ? m.team_a : m.team_b).map(getName),
                            scoreA: m.score_a!,
                            scoreB: m.score_b!,
                          });
                        }}
                        className="ml-3 text-xs underline text-gray-400 hover:text-nailong-orange transition"
                      >
                        签订投降书
                      </button>
                      {predictionResults.some(r => r.matchId === m.id && r.verdict === "wrong") && (
                        <span className="ml-2 inline-block px-2 py-0.5 rounded-full bg-purple-100 text-purple-600 text-[10px] font-bold animate-pulse">
                          毒奶!
                        </span>
                      )}
                    </div>
                  )}

                  {/* Inline scoring controls */}
                  {comp.status === "in_progress" && (
                    <div className="mt-4 space-y-3">
                      {scoreError && scoreError.matchId === m.id && (
                        <div className="text-center text-red-400 text-xs font-medium bg-red-50 rounded-lg py-1.5 px-3 animate-pulse">
                          {scoreError.message}
                        </div>
                      )}
                      <div className="flex items-center justify-end">
                        <button onClick={() => setEditing({ matchId: m.id, scoreA: String(m.score_a ?? 0), scoreB: String(m.score_b ?? 0) })}
                                className="text-xs text-nailong-orange hover:underline font-medium">
                          直接输入
                        </button>
                      </div>
                      <div className="flex items-center gap-3">
                        {/* Team A controls */}
                        <div className="flex-1 flex items-center justify-center gap-2">
                          <button onClick={() => handleMinusOne(m.id, "a")} disabled={!scored || m.score_a === 0}
                                  className="w-10 h-10 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed text-lg font-bold transition">
                            -
                          </button>
                          <button onClick={() => handlePlusOne(m.id, "a")} disabled={disabled}
                                  className="w-14 h-14 rounded-full bg-nailong-orange text-white hover:bg-nailong-orange-dark disabled:opacity-30 disabled:cursor-not-allowed text-2xl font-bold shadow-nailong transition active:scale-95">
                            +
                          </button>
                        </div>
                        <span className="text-gray-300 text-xs">计分</span>
                        {/* Team B controls */}
                        <div className="flex-1 flex items-center justify-center gap-2">
                          <button onClick={() => handlePlusOne(m.id, "b")} disabled={disabled}
                                  className="w-14 h-14 rounded-full bg-nailong-orange text-white hover:bg-nailong-orange-dark disabled:opacity-30 disabled:cursor-not-allowed text-2xl font-bold shadow-nailong transition active:scale-95">
                            +
                          </button>
                          <button onClick={() => handleMinusOne(m.id, "b")} disabled={!scored || m.score_b === 0}
                                  className="w-10 h-10 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed text-lg font-bold transition">
                            -
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Edit score dropdown panel */}
      {editing && (
        <div className="fixed inset-0 z-50" onClick={() => { setEditing(null); setEditError(""); }}>
          <div className="absolute inset-x-0 top-0 bg-white shadow-nailong border-b border-nailong-cream-dark p-6 animate-nailong-slide-down" onClick={e => e.stopPropagation()}>
            <div className="max-w-md mx-auto space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg text-gray-800">修改比分</h3>
                <button onClick={() => { setEditing(null); setEditError(""); }} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
              </div>
              <div className="flex gap-4 items-center justify-center py-2">
                <input value={editing.scoreA} onChange={e => setEditing({ ...editing, scoreA: e.target.value })}
                       className="w-20 border-2 border-nailong-cream-dark p-3 rounded-2xl text-center text-xl font-bold focus:border-nailong-yellow focus:ring-2 focus:ring-nailong-cream outline-none" autoFocus />
                <span className="text-2xl text-gray-300 font-bold">:</span>
                <input value={editing.scoreB} onChange={e => setEditing({ ...editing, scoreB: e.target.value })}
                       className="w-20 border-2 border-nailong-cream-dark p-3 rounded-2xl text-center text-xl font-bold focus:border-nailong-yellow focus:ring-2 focus:ring-nailong-cream outline-none" />
              </div>
              {editError && <div className="text-red-500 text-sm text-center bg-red-50 rounded-xl py-2">{editError}</div>}
              <div className="flex gap-3">
                <button onClick={handleEdit} className="btn-nailong flex-1">确认</button>
                <button onClick={() => { setEditing(null); setEditError(""); }} className="flex-1 bg-gray-100 py-3 rounded-[30px] font-medium text-gray-600 hover:bg-gray-200 transition">取消</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Finish confirm dropdown */}
      {finishing && (
        <div className="fixed inset-0 z-50" onClick={() => setFinishing(false)}>
          <div className="absolute inset-x-0 top-0 bg-white shadow-nailong border-b border-nailong-cream-dark p-6 animate-nailong-slide-down" onClick={e => e.stopPropagation()}>
            <div className="max-w-md mx-auto space-y-4 text-center">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg text-gray-800">结束比赛</h3>
                <button onClick={() => setFinishing(false)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
              </div>
              <p className="text-gray-500 text-sm">确认结束本场比赛吗？结束后仍可修改比分。</p>
              <div className="flex gap-3">
                <button onClick={handleFinish} className="btn-nailong flex-1">确认结束</button>
                <button onClick={() => setFinishing(false)} className="flex-1 bg-gray-100 py-3 rounded-[30px] font-medium text-gray-600 hover:bg-gray-200 transition">取消</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Surrender card modal */}
      {surrender && (
        <SurrenderCard
          show={!!surrender}
          onClose={() => setSurrender(null)}
          loserNames={surrender.loserNames}
          winnerNames={surrender.winnerNames}
          scoreA={surrender.scoreA}
          scoreB={surrender.scoreB}
          competitionName={comp.name}
        />
      )}

      {/* Share card modal */}
      {shareOpen && (
        <ShareCard
          show={shareOpen}
          onClose={() => setShareOpen(false)}
          competitionName={comp.name}
          rankedPlayers={ranked.map((s, i) => ({
            name: s.name,
            wins: s.wins,
            losses: s.losses,
            pointDiff: s.pointDiff,
            rank: i + 1,
          }))}
        />
      )}

      {/* Prediction card modal */}
      {predictionOpen && (
        <PredictionCard
          show={predictionOpen}
          onClose={() => setPredictionOpen(false)}
          competitionId={comp.id}
          competitionName={comp.name}
          players={comp.players}
          getName={getName}
        />
      )}
    </div>
  );
}
