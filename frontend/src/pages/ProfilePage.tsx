import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import client from "../api/client";

interface UserStats {
  win_rate: number;
  total_matches: number;
  wins: number;
}

const SKILL_LEVELS: { level: number; label: string; desc: string }[] = [
  { level: 1, label: "1级", desc: "能规范上场，懂基础规则与简单战术意识" },
  { level: 2, label: "2级", desc: "掌握高远球、发球等基本技术，可完成简单对抗" },
  { level: 3, label: "3级", desc: "技术逐步稳定，能控制落点，具备基础步法" },
  { level: 4, label: "4级", desc: "技术较全面（杀/吊/网前），比赛经验较丰富" },
  { level: 5, label: "5级", desc: "技术全面，战术意识强，业余俱乐部主力水平" },
  { level: 6, label: "6级", desc: "接近半专业，有系统训练背景，业余顶尖" },
  { level: 7, label: "7级", desc: "半专业/专业退役，市级比赛有竞争力" },
  { level: 8, label: "8级", desc: "现役省队/体校主力水平" },
  { level: 9, label: "9级", desc: "国家队/职业运动员水平" },
];

const GENDER_OPTIONS = [
  { value: "", label: "未设置" },
  { value: "男", label: "男" },
  { value: "女", label: "女" },
];

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [stats, setStats] = useState<UserStats>({ win_rate: 0, total_matches: 0, wins: 0 });
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showRules, setShowRules] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [gender, setGender] = useState("");
  const [skillLevel, setSkillLevel] = useState(0);
  const [birthYear, setBirthYear] = useState(0);
  const [bio, setBio] = useState("");

  useEffect(() => {
    client.get("/auth/me/stats").then(res => setStats(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (user) {
      setName(user.name);
      setGender(user.gender || "");
      setSkillLevel(user.skill_level || 0);
      setBirthYear(user.birth_year || 0);
      setBio(user.bio || "");
    }
  }, [user]);

  const [saveError, setSaveError] = useState("");

  const handleSave = async () => {
    setSaving(true);
    setSaveError("");
    try {
      await client.put("/auth/me", {
        name,
        gender,
        skill_level: skillLevel,
        birth_year: birthYear || 0,  // 空值转为 0 表示未设置
        bio,
      });
      await refreshUser();
      setEditing(false);
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || "保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  const currentYear = new Date().getFullYear();
  const age = birthYear > 1900 ? currentYear - birthYear : null;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">个人主页</h1>

      {/* Basic info card */}
      <div className="card-nailong p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            基本信息
          </h2>
          {!editing ? (
            <button
              onClick={() => setEditing(true)}
              className="text-sm text-nailong-orange font-medium hover:underline"
            >
              编辑
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => {
                  if (user) {
                    setName(user.name);
                    setGender(user.gender || "");
                    setSkillLevel(user.skill_level || 0);
                    setBirthYear(user.birth_year || 0);
                    setBio(user.bio || "");
                  }
                  setEditing(false);
                }}
                className="text-sm text-gray-400 font-medium hover:underline"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !name.trim()}
                className="btn-nailong text-sm py-1.5 px-4 disabled:opacity-50"
              >
                {saving ? "保存中..." : "保存"}
              </button>
            </div>
          )}
        </div>

        {editing ? (
          /* Edit mode */
          <div className="space-y-4">
            {saveError && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-2xl text-sm flex items-center justify-between">
                <span>{saveError}</span>
                <button onClick={() => setSaveError("")} className="text-red-400 hover:text-red-700">&times;</button>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">姓名 *</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                className="input-nailong"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">性别</label>
                <select
                  value={gender}
                  onChange={e => setGender(e.target.value)}
                  className="input-nailong"
                >
                  {GENDER_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">出生年份</label>
                <input
                  type="number"
                  value={birthYear || ""}
                  onChange={e => setBirthYear(Number(e.target.value))}
                  placeholder="如 1995"
                  className="input-nailong"
                  min={1900}
                  max={currentYear}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                中羽等级
                <button
                  type="button"
                  onClick={() => setShowRules(!showRules)}
                  className="ml-2 text-xs text-nailong-orange hover:underline font-normal"
                >
                  {showRules ? "收起规则" : "查看评级规则"}
                </button>
              </label>
              <select
                value={skillLevel}
                onChange={e => setSkillLevel(Number(e.target.value))}
                className="input-nailong"
              >
                <option value={0}>未设置</option>
                {SKILL_LEVELS.map(s => (
                  <option key={s.level} value={s.level}>
                    {s.label} - {s.desc}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">个人简介</label>
              <textarea
                value={bio}
                onChange={e => setBio(e.target.value)}
                placeholder="一句话介绍自己..."
                className="input-nailong resize-none"
                rows={2}
                maxLength={200}
              />
              <p className="text-xs text-gray-400 mt-1 text-right">{bio.length}/200</p>
            </div>
          </div>
        ) : (
          /* View mode */
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <img
                src="https://www.nailoong.com/img/ipStar/image_nailoong.png"
                alt="奶龙"
                className="w-14 h-14 object-contain animate-nailong-bounce-gentle"
              />
              <div>
                <div className="text-lg font-bold text-gray-800">
                  {user?.name}
                  {gender && (
                    <span className="ml-2 text-sm font-normal text-gray-400">
                      {gender === "男" ? "♂" : "♀"}
                    </span>
                  )}
                </div>
                <div className="text-sm text-nailong-orange">@{user?.username}</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm pt-2 border-t border-nailong-cream-dark">
              <div className="flex justify-between py-1">
                <span className="text-gray-400">中羽等级</span>
                <span className={`font-medium ${skillLevel > 0 ? "text-nailong-orange" : "text-gray-400"}`}>
                  {skillLevel > 0 ? `${skillLevel}级` : "未设置"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-gray-400">年龄</span>
                <span className="font-medium text-gray-700">
                  {age ? `${age}岁` : birthYear > 0 ? `${birthYear}年` : "未设置"}
                </span>
              </div>
            </div>
            {bio && (
              <p className="text-sm text-gray-600 bg-nailong-cream rounded-xl p-3 mt-2">{bio}</p>
            )}
          </div>
        )}
      </div>

      {/* Stats card */}
      <div className="card-nailong p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">比赛统计</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-nailong-cream p-4 rounded-2xl text-center">
            <div className="text-2xl font-bold text-nailong-orange">
              {(stats.win_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-400 mt-1">胜率</div>
          </div>
          <div className="bg-nailong-cream p-4 rounded-2xl text-center">
            <div className="text-2xl font-bold text-nailong-orange">{stats.wins}</div>
            <div className="text-xs text-gray-400 mt-1">胜场</div>
          </div>
          <div className="bg-nailong-cream p-4 rounded-2xl text-center">
            <div className="text-2xl font-bold text-nailong-orange">{stats.total_matches}</div>
            <div className="text-xs text-gray-400 mt-1">总局数</div>
          </div>
        </div>
      </div>

      {/* Skill level rules */}
      {showRules && (
        <div className="card-nailong p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">中羽等级评定规则</h2>
          <div className="space-y-2">
            {SKILL_LEVELS.map(s => (
              <div
                key={s.level}
                className={`flex items-start gap-3 p-3 rounded-xl transition ${
                  skillLevel === s.level
                    ? "bg-nailong-orange/10 border border-nailong-orange"
                    : "bg-nailong-cream"
                }`}
              >
                <span className={`shrink-0 w-10 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  skillLevel === s.level
                    ? "bg-nailong-orange text-white"
                    : "bg-white text-gray-500 border border-nailong-cream-dark"
                }`}>
                  {s.label}
                </span>
                <span className="text-sm text-gray-700 pt-0.5">{s.desc}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-xl">
            <p className="text-xs text-yellow-700 leading-relaxed">
              ⚠️ 该标准仅作科普参考，实际水平判定需结合技术稳定性、参赛经历、专业训练背景综合评估，非官方认证标准。
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
