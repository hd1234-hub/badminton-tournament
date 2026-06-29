import { useImageExport } from "../hooks/useImageExport";

interface SurrenderCardProps {
  show: boolean;
  onClose: () => void;
  loserNames: string[];
  winnerNames: string[];
  scoreA: number;
  scoreB: number;
  competitionName: string;
}

export default function SurrenderCard({
  show, onClose, loserNames, winnerNames, scoreA, scoreB, competitionName,
}: SurrenderCardProps) {
  const { exportRef, captureAndDownload } = useImageExport();
  if (!show) return null;

  const today = new Date().toLocaleDateString("zh-CN");
  const loserText = loserNames.join(" / ");
  const winnerText = winnerNames.join(" / ");
  const filename = `投降书_${loserNames.join("_")}`;

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-white shadow-nailong border-l border-nailong-cream-dark overflow-hidden animate-nailong-slide-left" onClick={e => e.stopPropagation()}>
        {/* Export card */}
        <div ref={exportRef} className="p-6 bg-gradient-to-b from-nailong-cream to-white">
          <div className="text-center mb-4">
            <img src="https://www.nailoong.com/img/ipStar/image_nailoong.png" alt="奶龙" className="w-16 h-16 mx-auto object-contain animate-nailong-bounce-gentle" />
            <h2 className="text-xl font-extrabold text-gray-800 mt-2">自愿投降书</h2>
            <p className="text-xs text-gray-400 mt-1">本场比赛战败方自愿签订此投降书</p>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center py-2 px-4 bg-red-50 rounded-2xl">
              <span className="text-gray-500">投降方</span>
              <span className="font-bold text-red-500">{loserText}</span>
            </div>
            <div className="flex justify-between items-center py-2 px-4 bg-green-50 rounded-2xl">
              <span className="text-gray-500">战胜方</span>
              <span className="font-bold text-green-600">{winnerText}</span>
            </div>
            <div className="text-center py-3">
              <span className="text-3xl font-black text-gray-800 tracking-widest">{scoreA} : {scoreB}</span>
            </div>
            <div className="flex justify-between text-xs text-gray-400 px-1">
              <span>{competitionName}</span>
              <span>{today}</span>
            </div>
            <div className="bg-nailong-cream rounded-2xl p-3 text-xs text-gray-600 leading-relaxed text-center">
              我等技不如人，甘拜下风，特此签订投降书，以表敬意。<br />下次再战，定当全力以赴！
            </div>
          </div>

          <p className="text-center text-[10px] text-gray-300 mt-4">奶龙羽毛球赛事系统</p>
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
