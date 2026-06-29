import { useState } from "react";
import type { Player, Prediction } from "../types";

const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) || "/api/v1").replace(/\/$/, "");

const NAILOONG_IMG = "https://www.nailoong.com/img/ipStar/image_nailoong.png";
const NAILOONG_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45' fill='%23FFB347'/%3E%3Ccircle cx='35' cy='40' r='8' fill='white'/%3E%3Ccircle cx='65' cy='40' r='8' fill='white'/%3E%3Ccircle cx='35' cy='42' r='3' fill='%23333'/%3E%3Ccircle cx='65' cy='42' r='3' fill='%23333'/%3E%3Cpath d='M35 60 Q50 75 65 60' stroke='%23333' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3C/svg%3E";

interface PredictionCardProps {
  show: boolean;
  onClose: () => void;
  competitionId: number;
  competitionName: string;
  players: Player[];
  getName: (id: number) => string;
}

const STORAGE_KEY = "nailong-predictions";

function loadPredictions(): Prediction[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function savePredictions(preds: Prediction[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(preds));
}

function extractPredictedWinner(text: string, nameA: string, nameB: string): string {
  // 直接查找"我预测XXX会赢"模式
  const match = text.match(/我预测\s*(\S+?)\s*会赢/);
  if (match) return match[1];

  // 查找"XXX会赢"模式
  const match2 = text.match(/(\S+?)\s*会赢/);
  if (match2) return match2[1];

  // 统计名字出现次数作为备选
  const countA = (text.match(new RegExp(nameA, "g")) || []).length;
  const countB = (text.match(new RegExp(nameB, "g")) || []).length;
  if (countA > countB) return nameA;
  if (countB > countA) return nameB;
  return "";
}

export function resolvePredictions(
  matchId: number,
  teamA: number[],
  teamB: number[],
  scoreA: number,
  scoreB: number,
  getName: (id: number) => string,
): Array<{ matchId: number; predictionId: string; predictedWinner: string; actualWinner: string; verdict: "correct" | "wrong" }> {
  const predictions = loadPredictions();
  let changed = false;
  const results: Array<{ matchId: number; predictionId: string; predictedWinner: string; actualWinner: string; verdict: "correct" | "wrong" }> = [];

  const sideAWon = scoreA > scoreB;
  const actualWinnerNames = sideAWon ? teamA.map(getName) : teamB.map(getName);

  for (const p of predictions) {
    if (p.verdict !== "pending") continue;
    const aInTeamA = teamA.includes(p.playerAId);
    const bInTeamA = teamA.includes(p.playerBId);
    const aInTeamB = teamB.includes(p.playerAId);
    const bInTeamB = teamB.includes(p.playerBId);
    const onOppositeSides = (aInTeamA && bInTeamB) || (aInTeamB && bInTeamA);
    if (!onOppositeSides) continue;

    p.matchId = matchId;
    p.actualWinner = actualWinnerNames[0] || "";
    p.verdict = actualWinnerNames.includes(p.predictedWinner) ? "correct" : "wrong";
    changed = true;
    results.push({
      matchId,
      predictionId: p.id,
      predictedWinner: p.predictedWinner,
      actualWinner: p.actualWinner,
      verdict: p.verdict,
    });
  }

  if (changed) savePredictions(predictions);
  return results;
}

export default function PredictionCard({ show, onClose, competitionId, competitionName, players, getName }: PredictionCardProps) {
  const [playerA, setPlayerA] = useState<number | null>(null);
  const [playerB, setPlayerB] = useState<number | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [predictionText, setPredictionText] = useState("");
  const [predictedWinner, setPredictedWinner] = useState("");
  const [history, setHistory] = useState<Prediction[]>(() =>
    loadPredictions().filter(p => p.competitionId === competitionId),
  );

  if (!show) return null;

  const selectedA = players.find(p => p.id === playerA);
  const selectedB = players.find(p => p.id === playerB);

  const handlePredict = async () => {
    if (!selectedA || !selectedB || streaming) return;
    setStreaming(true);
    setPredictionText("");
    setPredictedWinner("");

    const token = localStorage.getItem("token");
    if (!token) {
      setPredictionText("请先登录");
      setStreaming(false);
      return;
    }

    const prompt = `请直接以奶龙的口吻，预测一下 ${selectedA.name} 和 ${selectedB.name} 之间的单打比赛谁会赢。请不要调用任何工具，直接给出你的分析预测。先简要分析双方的特点，然后给出你的预测结论，要风趣幽默一些，最后必须明确说"我预测XXX会赢"。`;

    try {
      const response = await fetch(`${API_BASE}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: prompt }),
      });

      const reader = response.body?.getReader();
      if (!reader) throw new Error("连接失败");
      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const data = await response.json();
          detail = data?.detail || detail;
        } catch {
          // ignore json parse failures
        }
        throw new Error(detail);
      }

      const decoder = new TextDecoder();
      let fullText = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const parsed = JSON.parse(line.slice(6));
            if (parsed.type === "text") {
              fullText += parsed.content;
              setPredictionText(fullText);
            } else if (parsed.type === "error") {
              // 显示错误信息但不中断
              fullText += parsed.content || "";
              setPredictionText(fullText);
            }
          } catch { /* skip */ }
        }
      }

      // Extract predicted winner
      const winner = extractPredictedWinner(fullText, selectedA.name, selectedB.name);
      setPredictedWinner(winner);

      // Save prediction
      const pred: Prediction = {
        id: `${competitionId}-${Date.now()}`,
        competitionId,
        competitionName,
        playerAId: selectedA.id,
        playerAName: selectedA.name,
        playerBId: selectedB.id,
        playerBName: selectedB.name,
        predictedWinner: winner,
        predictedText: fullText,
        matchId: null,
        actualWinner: null,
        verdict: "pending",
        createdAt: new Date().toISOString(),
      };
      const all = loadPredictions();
      all.push(pred);
      savePredictions(all);
      setHistory(prev => [pred, ...prev]);
    } catch (e: any) {
      const msg = e?.message ? `连接失败：${e.message}` : "连接失败，请确认后端已启动";
      setPredictionText(msg);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-white shadow-nailong border-l border-nailong-cream-dark flex flex-col overflow-hidden animate-nailong-slide-left" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="p-4 border-b border-nailong-cream-dark bg-nailong-cream flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src={NAILOONG_IMG} alt="奶龙" className="w-8 h-8 object-contain" onError={e => { (e.target as HTMLImageElement).src = NAILOONG_FALLBACK; }} />
            <span className="font-bold text-gray-800">毒奶预测</span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Player selection */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">球员 A</label>
              <select
                value={playerA ?? ""}
                onChange={e => setPlayerA(Number(e.target.value) || null)}
                className="input-nailong text-sm"
                disabled={streaming}
              >
                <option value="">选择球员</option>
                {players.filter(p => p.id !== playerB).map(p => (
                  <option key={p.id} value={p.id}>{p.name} (Lv.{p.level || "?"})</option>
                ))}
              </select>
            </div>
            <div className="text-center text-gray-300 text-sm font-bold">VS</div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">球员 B</label>
              <select
                value={playerB ?? ""}
                onChange={e => setPlayerB(Number(e.target.value) || null)}
                className="input-nailong text-sm"
                disabled={streaming}
              >
                <option value="">选择球员</option>
                {players.filter(p => p.id !== playerA).map(p => (
                  <option key={p.id} value={p.id}>{p.name} (Lv.{p.level || "?"})</option>
                ))}
              </select>
            </div>
            <button
              onClick={handlePredict}
              disabled={!playerA || !playerB || streaming}
              className="btn-nailong w-full text-sm disabled:opacity-50"
            >
              {streaming ? "奶龙正在预测..." : "开始预测"}
            </button>
          </div>

          {/* Prediction result */}
          {(predictionText || streaming) && (
            <div className="bg-purple-50 rounded-2xl p-4 border border-purple-100">
              <div className="flex items-center gap-2 mb-2">
                <img src={NAILOONG_IMG} alt="奶龙" className="w-6 h-6 object-contain animate-nailong-bounce-gentle" onError={e => { (e.target as HTMLImageElement).src = NAILOONG_FALLBACK; }} />
                <span className="text-xs font-semibold text-purple-600">奶龙的毒奶分析</span>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {predictionText || (streaming ? "思考中..." : "")}
              </p>
              {predictedWinner && (
                <div className="mt-3 text-center">
                  <span className="badge-nailong text-xs">
                    预测胜者：{predictedWinner}
                    {!predictedWinner ? " (奶龙不敢下结论...)" : ""}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-2">预测历史</h4>
              <div className="space-y-2">
                {history.slice(0, 10).map(p => (
                  <div key={p.id} className="flex items-center gap-2 text-xs bg-gray-50 rounded-xl p-2">
                    <span className="font-medium text-gray-700">{p.playerAName}</span>
                    <span className="text-gray-300">vs</span>
                    <span className="font-medium text-gray-700">{p.playerBName}</span>
                    <span className="ml-auto">
                      {p.verdict === "pending" ? (
                        <span className="text-gray-400">待定</span>
                      ) : p.verdict === "correct" ? (
                        <span className="text-green-500 font-medium">预测正确</span>
                      ) : (
                        <span className="text-purple-500 font-bold animate-pulse">毒奶!</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
