import { useImageExport } from "../hooks/useImageExport";

interface RankedPlayer {
  name: string;
  wins: number;
  losses: number;
  pointDiff: number;
  rank: number;
}

interface ShareCardProps {
  show: boolean;
  onClose: () => void;
  competitionName: string;
  rankedPlayers: RankedPlayer[];
}

function rankBadge(rank: number) {
  if (rank === 1) return "bg-yellow-400 text-white";
  if (rank === 2) return "bg-gray-300 text-white";
  if (rank === 3) return "bg-orange-300 text-white";
  return "bg-gray-100 text-gray-500";
}

export default function ShareCard({ show, onClose, competitionName, rankedPlayers }: ShareCardProps) {
  const { exportRef, captureAndDownload } = useImageExport();
  if (!show) return null;

  const today = new Date().toLocaleDateString("zh-CN");
  const filename = `战绩分享_${competitionName}`;

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-white shadow-nailong border-l border-nailong-cream-dark overflow-hidden animate-nailong-slide-left" onClick={e => e.stopPropagation()}>
        {/* Export card */}
        <div ref={exportRef} className="p-6 bg-gradient-to-b from-nailong-cream via-white to-yellow-50">
          <div className="text-center mb-4">
            <img src="https://www.nailoong.com/img/ipStar/image_nailoong.png" alt="奶龙" className="w-14 h-14 mx-auto object-contain animate-nailong-bounce-gentle" />
            <h2 className="text-lg font-extrabold text-gray-800 mt-1">赛后战绩分享</h2>
            <p className="text-sm font-semibold text-nailong-orange mt-1">{competitionName}</p>
            <p className="text-xs text-gray-400 mt-0.5">{today}</p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-[10px] text-gray-400 px-2 mb-1">
              <span className="w-8 text-center">排名</span>
              <span className="flex-1">球员</span>
              <span className="w-8 text-center">胜</span>
              <span className="w-8 text-center">负</span>
              <span className="w-10 text-center">净胜</span>
            </div>
            {rankedPlayers.slice(0, 8).map(p => (
              <div key={p.rank} className={`flex items-center gap-2 px-2 py-1.5 rounded-xl text-xs ${p.rank <= 3 ? "bg-nailong-cream" : ""}`}>
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${rankBadge(p.rank)}`}>
                  {p.rank}
                </span>
                <span className="flex-1 font-medium text-gray-800 truncate">{p.name}</span>
                <span className="w-8 text-center font-semibold text-green-600">{p.wins}</span>
                <span className="w-8 text-center text-red-400">{p.losses}</span>
                <span className={`w-10 text-center font-bold ${p.pointDiff > 0 ? "text-nailong-orange" : p.pointDiff < 0 ? "text-gray-400" : "text-gray-500"}`}>
                  {p.pointDiff > 0 ? "+" : ""}{p.pointDiff}
                </span>
              </div>
            ))}
          </div>

          <p className="text-center text-[10px] text-gray-300 mt-4">奶龙羽毛球 · 用心记录每一场对决</p>
        </div>

        {/* Actions */}
        <div className="flex gap-3 p-4 border-t border-nailong-cream-dark">
          <button onClick={() => captureAndDownload(filename)} className="btn-nailong flex-1 text-sm">
            下载 PNG
          </button>
          <button onClick={onClose} className="flex-1 py-3 rounded-[30px] bg-gray-100 text-gray-500 text-sm font-medium hover:bg-gray-200 transition">
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
