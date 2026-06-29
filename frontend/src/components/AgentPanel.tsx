import { useState, useRef, useEffect, useCallback, type MouseEvent as ReactMouseEvent, type TouchEvent as ReactTouchEvent } from "react";
import { Link } from "react-router-dom";
import * as clubsApi from "../api/clubs";
import type { Club } from "../types";

const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) || "/api/v1").replace(/\/$/, "");

const NAILOONG_SOURCES = [
  "https://www.nailoong.com/img/business/nl_base_3d.png",
  "https://c-ssl.dtstatic.com/uploads/blog/202206/02/20220602221208_b4253.thumb.1000_0.gif",
];

const NAILOONG_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45' fill='%23FFB347'/%3E%3Ccircle cx='35' cy='40' r='8' fill='white'/%3E%3Ccircle cx='65' cy='40' r='8' fill='white'/%3E%3Ccircle cx='35' cy='42' r='3' fill='%23333'/%3E%3Ccircle cx='65' cy='42' r='3' fill='%23333'/%3E%3Cpath d='M35 60 Q50 75 65 60' stroke='%23333' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3C/svg%3E";

const MESSAGES_STORAGE_KEY = "nailong-agent-messages";
const CONTEXT_STORAGE_KEY = "nailong-agent-context";

function getNailoongSrc(index: number) {
  return NAILOONG_SOURCES[index % NAILOONG_SOURCES.length];
}

function NailoongImg({ index, className }: { index: number; className?: string }) {
  const [imgError, setImgError] = useState(false);
  const src = getNailoongSrc(index);
  if (imgError) {
    return <img src={NAILOONG_FALLBACK} alt="奶龙" className={className} />;
  }
  return <img src={src} alt="奶龙" className={className} onError={() => setImgError(true)} />;
}

// 过滤掉 AI 回复中的 markdown 格式符号（**粗体**、*斜体* 等）
function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/`(.+?)`/g, "$1");
}

interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

interface NavLink {
  label: string;
  path: string;
}

interface ChatMessage {
  role: "user" | "agent";
  content: string;
  toolCalls?: ToolCall[];
  navLinks?: NavLink[];
  toolRound?: number;  // 多轮工具调用轮次
}

interface AgentContext {
  clubId?: number;
  compId?: number;
}

export default function AgentPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem(MESSAGES_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved) as ChatMessage[];
      } catch {
        /* ignore */
      }
    }
    return [
      { role: "agent", content: "嗨~ 我是奶龙，你的专属球场伙伴！\n\n有啥需要尽管跟我说：\n  · 看看你的俱乐部和球员\n  · 帮你组织一场比赛\n  · 查排名、分析搭档\n  · 毒奶预测胜负\n\n先告诉我你有哪个俱乐部？我帮你盯着~" },
    ];
  });
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [listening, setListening] = useState(false);
  const [ctx, setCtx] = useState<AgentContext>(() => {
    const saved = localStorage.getItem(CONTEXT_STORAGE_KEY);
    if (saved) {
      try {
        return JSON.parse(saved) as AgentContext;
      } catch {
        /* ignore */
      }
    }
    return {};
  });
  const [position, setPosition] = useState({
    x: Math.max(window.innerWidth - 420, 16),
    y: 72,
  });
  const [dragging, setDragging] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [memoryStats, setMemoryStats] = useState<{
    total_messages: number; user_messages: number; agent_messages: number;
    summaries: number; recent_topics: string[]; storage: string;
  } | null>(null);
  const [clubs, setClubs] = useState<Club[]>([]);
  const dragOffsetRef = useRef({ x: 0, y: 0 });
  const endRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
    localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages.slice(-40)));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(ctx));
  }, [ctx]);

  useEffect(() => {
    clubsApi.listClubs().then(setClubs).catch(() => {});
  }, []);

  useEffect(() => {
    if (!dragging) return;

    const onMove = (event: MouseEvent | TouchEvent) => {
      const clientX = "touches" in event ? event.touches[0].clientX : event.clientX;
      const clientY = "touches" in event ? event.touches[0].clientY : event.clientY;
      setPosition({
        x: Math.min(Math.max(clientX - dragOffsetRef.current.x, 16), window.innerWidth - 300),
        y: Math.min(Math.max(clientY - dragOffsetRef.current.y, 16), window.innerHeight - 120),
      });
    };

    const onUp = () => setDragging(false);

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("touchmove", onMove, { passive: false });
    window.addEventListener("touchend", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("touchend", onUp);
    };
  }, [dragging]);

  const startDrag = (event: ReactMouseEvent<HTMLDivElement>) => {
    setDragging(true);
    dragOffsetRef.current = {
      x: event.clientX - position.x,
      y: event.clientY - position.y,
    };
  };

  const startDragTouch = (event: ReactTouchEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(true);
    dragOffsetRef.current = {
      x: event.touches[0].clientX - position.x,
      y: event.touches[0].clientY - position.y,
    };
  };

  const quickPrompt = ["帮我看看记忆系统", "给我推荐一个俱乐部玩法", "把比赛记录一下", "毒奶预测一下"];

  const sendPreset = (prompt: string) => {
    setInput(prompt);
  };

  const clearMemory = () => {
    // 清空远程记忆
    const token = localStorage.getItem("token");
    if (token) {
      fetch(`${API_BASE}/agent/memory`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
        .catch(() => {});
    }
    // 同时清空本地
    localStorage.removeItem(MESSAGES_STORAGE_KEY);
    localStorage.removeItem(CONTEXT_STORAGE_KEY);
    setCtx({});
    setMemoryStats(null);
    setMessages([
      { role: "agent", content: "记忆已清空。接下来我们重新开始。" },
    ]);
  };

  const fetchMemoryStats = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/agent/memory`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setMemoryStats(data.stats);
      }
    } catch { /* ignore */ }
  };

  const extractContext = useCallback((toolCalls: ToolCall[]) => {
    setCtx(prev => {
      const next = { ...prev };
      for (const tc of toolCalls) {
        if (tc.name === "create_competition" || tc.name === "get_competition") {
          // context extracted from subsequent response, not tool args
        }
        if (tc.name === "get_club_players" || tc.name === "get_leaderboard") {
          if (tc.args.club_id) next.clubId = Number(tc.args.club_id);
        }
      }
      return next;
    });
  }, []);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || streaming) return;

    // 只在用户没有明确指定俱乐部/比赛时，附加上下文提示
    const contextParts: string[] = [];
    if (ctx.clubId && !text.match(/俱乐部|club/)) contextParts.push(`当前俱乐部ID=${ctx.clubId}`);
    if (ctx.compId && !text.match(/比赛|competition|comp/)) contextParts.push(`当前比赛ID=${ctx.compId}`);
    const contextSuffix = contextParts.length > 0 ? `\n（提示：${contextParts.join("，")}，如需切换请直接说"切换到XX俱乐部"）` : "";
    const fullMessage = text + contextSuffix;

    setMessages(prev => [...prev, { role: "user", content: text }]);
    setInput("");
    setStreaming(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setMessages(prev => [...prev, { role: "agent", content: "请先登录" }]);
      setStreaming(false);
      return;
    }

    try {
      // 构建历史消息（最近 10 轮对话）
      const history = messages.slice(-20).map(m => ({
        role: m.role === "agent" ? "assistant" : "user",
        content: m.content,
      }));

      const response = await fetch(`${API_BASE}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: fullMessage, history }),
      });

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader");
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
      let agentContent = "";
      const toolCalls: ToolCall[] = [];
      const navLinks: NavLink[] = [];
      let buffer = "";
      let currentToolRound = 0;  // 当前工具调用轮次

      setMessages(prev => [...prev, { role: "agent", content: "", toolCalls: [], toolRound: 0 }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === "text") {
              agentContent += parsed.content;
              const displayContent = stripMarkdown(agentContent);
              // 从回复中提取 context
              const compMatch = agentContent.match(/比赛.*?ID[：:]\s*(\d+)/);
              const clubMatch = agentContent.match(/俱乐部.*?ID[：:]\s*(\d+)/);
              if (compMatch) setCtx(prev => ({ ...prev, compId: Number(compMatch[1]) }));
              if (clubMatch) setCtx(prev => ({ ...prev, clubId: Number(clubMatch[1]) }));

              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = { 
                  role: "agent", 
                  content: displayContent, 
                  toolCalls, 
                  navLinks,
                  toolRound: currentToolRound 
                };
                return copy;
              });
            } else if (parsed.type === "tool_call") {
              toolCalls.push({ name: parsed.name, args: parsed.args });
              currentToolRound = parsed.round || toolCalls.length;
              extractContext([{ name: parsed.name, args: parsed.args }]);
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = { 
                  role: "agent", 
                  content: stripMarkdown(agentContent), 
                  toolCalls, 
                  navLinks,
                  toolRound: currentToolRound 
                };
                return copy;
              });
            } else if (parsed.type === "nav_link") {
              navLinks.push({ label: parsed.label, path: parsed.path });
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = { 
                  role: "agent", 
                  content: stripMarkdown(agentContent), 
                  toolCalls, 
                  navLinks,
                  toolRound: currentToolRound 
                };
                return copy;
              });
            } else if (parsed.type === "error") {
              const msg = parsed.content || "AI 调用失败，请稍后重试";
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = {
                  role: "agent",
                  content: msg,
                  toolCalls,
                  navLinks,
                  toolRound: currentToolRound,
                };
                return copy;
              });
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (e: any) {
      const msg = e?.message ? `连接失败：${e.message}` : "连接失败，请确认后端已启动";
      setMessages(prev => [...prev, { role: "agent", content: msg }]);
    } finally {
      setStreaming(false);
    }
  };

  const [voiceError, setVoiceError] = useState<string | null>(null);
  const voiceTimeoutRef = useRef<number | null>(null);

  const clearVoiceTimeout = () => {
    if (voiceTimeoutRef.current) {
      window.clearTimeout(voiceTimeoutRef.current);
      voiceTimeoutRef.current = null;
    }
  };

  const startVoice = () => {
    setVoiceError(null);
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError("当前浏览器不支持语音输入，请使用 Chrome 或 Edge 浏览器");
      return;
    }

    // 检查是否在安全环境
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      setVoiceError("语音输入需要 HTTPS 环境，请使用 https 访问或本地开发");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "zh-CN";
      recognition.interimResults = true; // 开启中间结果，获得实时反馈
      recognition.continuous = false;    // 单次识别，说完自动停止
      recognition.maxAlternatives = 1;

      let finalTranscript = "";

      recognition.onstart = () => {
        setListening(true);
        setVoiceError(null);
        // 10秒超时保护
        voiceTimeoutRef.current = window.setTimeout(() => {
          if (recognitionRef.current) {
            recognitionRef.current.stop();
          }
        }, 10000);
      };

      recognition.onresult = (e: any) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) {
            finalTranscript += e.results[i][0].transcript;
          } else {
            interim += e.results[i][0].transcript;
          }
        }
        // 实时显示中间结果
        setInput(prev => finalTranscript + interim);
      };

      recognition.onerror = (e: any) => {
        clearVoiceTimeout();
        setListening(false);
        const errorMap: Record<string, string> = {
          'no-speech': '没听到声音，请再试一次',
          'audio-capture': '无法访问麦克风，请检查权限设置',
          'not-allowed': '麦克风权限被拒绝，请在浏览器设置中允许',
          'network': '网络问题，请检查连接后重试',
          'aborted': '已取消',
        };
        setVoiceError(errorMap[e.error] || `语音识别失败: ${e.error}`);
      };

      recognition.onend = () => {
        clearVoiceTimeout();
        setListening(false);
        // 如果有识别结果，保留到输入框
        if (finalTranscript) {
          setInput(finalTranscript);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setVoiceError("启动语音识别失败，请刷新页面重试");
    }
  };

  const stopVoice = () => {
    clearVoiceTimeout();
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore stop errors
    }
    setListening(false);
  };

  const toolLabels: Record<string, string> = {
    list_user_clubs: "查看俱乐部",
    create_club: "创建俱乐部",
    join_club: "加入俱乐部",
    search_clubs: "搜索俱乐部",
    list_available_clubs: "查看可加入俱乐部",
    get_club_players: "查看球员",
    create_competition: "创建比赛",
    list_open_competitions: "查看比赛大厅",
    join_open_competition: "报名比赛",
    start_competition: "开始比赛",
    list_my_competitions: "查看我的比赛",
    list_active_competitions: "查看进行中比赛",
    get_competition: "查看比赛",
    record_score: "录入比分",
    record_competition_score: "录入比赛比分",
    record_latest_score: "自动计分",
    get_leaderboard: "排行榜",
    get_partner_stats: "搭档分析",
    suggest_teams: "智能分组",
  };

  // 多轮工具调用时的进度提示
  const toolProgressHints: Record<string, string> = {
    create_competition: "正在创建比赛...",
    get_competition: "正在获取比赛信息...",
    record_score: "正在记录比分...",
    record_competition_score: "正在录入比赛比分...",
    record_latest_score: "正在自动识别比赛并计分...",
    list_active_competitions: "正在查找可计分比赛...",
    list_available_clubs: "正在查找可加入俱乐部...",
    list_open_competitions: "正在查询比赛大厅...",
    start_competition: "正在开始比赛...",
    get_leaderboard: "正在查询排行榜...",
    get_partner_stats: "正在分析搭档数据...",
    suggest_teams: "正在计算最佳分组...",
    create_club: "正在创建俱乐部...",
    join_club: "正在加入俱乐部...",
    search_clubs: "正在搜索俱乐部...",
  };

  // 检测是否为移动端
  const isMobile = window.innerWidth < 768;
  
  return (
    <div
      className={`fixed z-50 bg-white shadow-2xl flex flex-col border border-nailong-cream-dark rounded-[28px] overflow-hidden ${
        isMobile 
          ? 'w-[calc(100vw-32px)] left-4 right-4 top-20 bottom-4 max-h-[calc(100vh-120px)]' 
          : 'w-[380px] max-w-[calc(100vw-24px)]'
      }`}
      style={isMobile ? {} : { left: position.x, top: position.y, maxHeight: `calc(100vh - ${position.y}px - 16px)` }}
    >
      {/* Header */}
      <div
        className={`flex items-center justify-between p-4 border-b border-nailong-cream-dark bg-nailong-cream select-none ${isMobile ? 'cursor-default' : 'cursor-move'}`}
        onMouseDown={isMobile ? undefined : startDrag}
        onTouchStart={isMobile ? undefined : startDragTouch}
      >
        <div className="flex items-center gap-2">
          <NailoongImg index={0} className="w-10 h-10 object-contain animate-nailong-swing" />
          <div>
            <div className="font-bold text-gray-800">AI 助手</div>
            <div className="text-[11px] text-gray-500">可拖拽 · 奶龙陪聊</div>
          </div>
          {ctx.clubId && <span className="text-xs text-nailong-orange">#{ctx.clubId}</span>}
          {ctx.compId && <span className="text-xs text-nailong-orange">比赛#{ctx.compId}</span>}
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
      </div>

      {/* Club switcher */}
      {clubs.length > 0 && (
        <div className="px-4 pt-3 pb-1 bg-white">
          <select
            value={ctx.clubId ?? ""}
            onChange={e => {
              const val = e.target.value;
              setCtx(prev => ({ ...prev, clubId: val ? Number(val) : undefined }));
            }}
            className="input-nailong text-xs py-2"
          >
            <option value="">选择当前俱乐部（可选）</option>
            {clubs.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Quick actions */}
      <div className="px-4 pt-3 flex flex-wrap gap-2 bg-white">
        {quickPrompt.map(prompt => (
          <button key={prompt} onClick={() => sendPreset(prompt)} className="badge-nailong text-xs">
            {prompt}
          </button>
        ))}
        <button
          onClick={() => setMemoryOpen(!memoryOpen)}
          className={`text-xs px-3 py-1 rounded-capsule transition ${
            memoryOpen
              ? "bg-nailong-orange text-white"
              : "bg-gray-100 text-gray-500 hover:bg-gray-200"
          }`}
        >
          记忆 ({messages.length}条)
        </button>
        <button onClick={clearMemory} className="text-xs px-3 py-1 rounded-capsule bg-gray-100 text-gray-500 hover:bg-gray-200">
          清空
        </button>
      </div>

      {/* Memory panel */}
      {memoryOpen && (
        <div className="px-4 pt-2 pb-1 bg-white border-b border-nailong-cream-dark">
          <div className="bg-nailong-cream rounded-2xl p-3 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-700">奶龙的记忆</span>
              <button onClick={fetchMemoryStats} className="text-[10px] text-nailong-orange hover:underline">
                刷新
              </button>
            </div>
            <div className="space-y-1 text-gray-600">
              <div className="flex justify-between">
                <span>总消息</span>
                <span className="font-medium">{memoryStats?.total_messages ?? "加载中..."}</span>
              </div>
              <div className="flex justify-between">
                <span>我的消息</span>
                <span className="font-medium">{memoryStats?.user_messages ?? "-"}</span>
              </div>
              <div className="flex justify-between">
                <span>奶龙回复</span>
                <span className="font-medium">{memoryStats?.agent_messages ?? "-"}</span>
              </div>
              <div className="flex justify-between">
                <span>自动总结</span>
                <span className="font-medium">{memoryStats?.summaries ?? "-"} 条</span>
              </div>
              <div className="flex justify-between">
                <span>当前俱乐部</span>
                <span className={`font-medium ${ctx.clubId ? "text-nailong-orange" : "text-gray-400"}`}>
                  {ctx.clubId ? `#${ctx.clubId}` : "未设置"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>当前比赛</span>
                <span className={`font-medium ${ctx.compId ? "text-nailong-orange" : "text-gray-400"}`}>
                  {ctx.compId ? `#${ctx.compId}` : "未设置"}
                </span>
              </div>
              {memoryStats?.recent_topics && memoryStats.recent_topics.length > 0 && (
                <div className="pt-1 border-t border-nailong-cream-dark">
                  <span className="text-gray-400">近期话题</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {memoryStats.recent_topics.map(t => (
                      <span key={t} className="px-1.5 py-0.5 bg-white rounded text-[10px] text-nailong-orange">{t}</span>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex justify-between pt-1 border-t border-nailong-cream-dark">
                <span>存储位置</span>
                <span className="text-green-500 font-medium">{memoryStats?.storage ?? "加载中..."}</span>
              </div>
              <p className="text-[11px] text-gray-400">
                记忆自动分层：近期完整保留 · 远期智能总结
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: 'calc(100vh - 280px)', minHeight: '120px' }}>
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
              m.role === "user"
                ? "bg-nailong-orange text-white rounded-br-sm"
                : "bg-nailong-cream text-gray-800 rounded-bl-sm"
            }`}>
              {m.role === "agent" && (
                <NailoongImg index={i} className="w-12 h-12 object-contain mb-2 rounded-full animate-nailong-bounce-gentle" />
              )}
              <div className="whitespace-pre-wrap">{m.content || (streaming && i === messages.length - 1 ? "思考中..." : "")}</div>
              {m.toolCalls && m.toolCalls.length > 0 && (
                <div className="mt-2 space-y-1">
                  {m.toolCalls.map((tc, j, toolCalls) => (
                    <div key={j} className="flex items-center gap-2 text-xs">
                      <span className="text-nailong-orange">🔧</span>
                      <span className="text-gray-600">{toolLabels[tc.name] || tc.name}</span>
                      {/* 显示多轮进度 */}
                      {m.toolRound && m.toolRound > 1 && j === toolCalls.length - 1 && (
                        <span className="text-[10px] bg-nailong-cream px-2 py-0.5 rounded-full text-gray-500">
                          第{m.toolRound}步
                        </span>
                      )}
                    </div>
                  ))}
                  {/* 多轮工具调用总结 */}
                  {m.toolRound && m.toolRound > 1 && (
                    <div className="mt-1 text-[10px] text-gray-400 border-t border-nailong-cream-dark pt-1">
                      共执行 {m.toolCalls.length} 个步骤
                    </div>
                  )}
                </div>
              )}
              {m.navLinks && m.navLinks.length > 0 && (
                <div className="mt-2 pt-2 border-t border-nailong-cream-dark space-y-1">
                  {m.navLinks.map((nav, j) => (
                    <Link
                      key={j}
                      to={nav.path}
                      className="flex items-center gap-1 text-xs text-nailong-orange hover:text-nailong-orange-dark hover:underline font-medium"
                      onClick={onClose}
                    >
                      <span>🔗</span>
                      <span>{nav.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-nailong-cream-dark bg-white">
        {voiceError && (
          <div className="mb-3 px-4 py-2 bg-red-50 text-red-600 text-sm rounded-xl flex items-center justify-between">
            <span>{voiceError}</span>
            <button onClick={() => setVoiceError(null)} className="text-red-400 hover:text-red-700">&times;</button>
          </div>
        )}
        <div className="flex gap-2">
          <button
            onClick={listening ? stopVoice : startVoice}
            className={`px-3 py-3 rounded-2xl transition ${listening ? "bg-red-500 text-white animate-pulse" : "bg-nailong-cream text-gray-500 hover:bg-nailong-cream-dark"}`}
            title="语音输入">
            🎤
          </button>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
            placeholder="输入消息或语音..."
            className="input-nailong flex-1 text-sm"
            disabled={streaming}
          />
          <button
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            className="btn-nailong px-4 disabled:opacity-50">
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
