import { useEffect, useRef, useState } from "react";
import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { Notification } from "../types";
import * as notificationsApi from "../api/notifications";
import AgentPanel from "./AgentPanel";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [agentOpen, setAgentOpen] = useState(false);
  const [noticeOpen, setNoticeOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const noticeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (noticeRef.current && !noticeRef.current.contains(e.target as Node)) {
        setNoticeOpen(false);
      }
    };
    if (noticeOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [noticeOpen]);

  const loadNotifications = () => notificationsApi.listNotifications().then(setNotifications).catch(() => {});

  useEffect(() => {
    loadNotifications();
    const timer = window.setInterval(loadNotifications, 60000);
    return () => window.clearInterval(timer);
  }, []);

  const unreadCount = notifications.filter(n => !n.read_at).length;

  const handleNotificationClick = async (n: Notification) => {
    setNoticeOpen(false);
    try {
      await notificationsApi.markRead(n.id);
      loadNotifications();
    } catch {
      // 标记已读失败仍允许跳转
    }
    if (n.competition_id) {
      navigate(`/competitions/${n.competition_id}`);
    } else if (n.activity_id) {
      navigate(`/activities/${n.activity_id}`);
    } else if (n.club_id) {
      navigate(`/clubs/${n.club_id}`);
    } else {
      navigate("/my-competitions");
    }
  };

  return (
    <div className="min-h-screen bg-nailong-cream">
      <nav className="bg-white shadow-nailong px-4 md:px-6 py-3 flex justify-between items-center rounded-b-3xl">
        <Link to="/" className="text-lg md:text-xl font-bold text-nailong-orange flex items-center gap-2 shrink-0">
          <img src="https://www.nailoong.com/img/ipStar/image_nailoong.png" alt="奶龙" className="w-8 h-8 md:w-10 md:h-10 object-contain animate-nailong-swing" />
          <span className="hidden sm:inline">奶龙羽毛球</span>
          <span className="sm:hidden">羽毛球</span>
        </Link>
        <div className="flex items-center gap-2 md:gap-4 min-w-0">
          <div className="flex items-center gap-2 md:gap-4 overflow-x-auto no-scrollbar min-w-0">
            <button type="button" onClick={() => setAgentOpen(!agentOpen)}
                    className={`px-2 md:px-3 py-1.5 rounded-[30px] text-xs md:text-sm font-medium transition whitespace-nowrap ${agentOpen ? "bg-nailong-orange text-white" : "bg-nailong-cream text-gray-600 hover:bg-nailong-cream-dark"}`}>
              AI
            </button>
            <Link to="/my-competitions" className="text-gray-600 hover:text-nailong-orange font-medium transition-colors text-sm md:text-base whitespace-nowrap">比赛</Link>
            <Link to="/leaderboard" className="text-gray-600 hover:text-nailong-orange font-medium transition-colors text-sm md:text-base whitespace-nowrap">排行</Link>
            {user?.is_admin && (
              <Link to="/admin" className="text-gray-600 hover:text-nailong-orange font-medium transition-colors text-sm md:text-base whitespace-nowrap">运营</Link>
            )}
          </div>

          <div ref={noticeRef} className="relative shrink-0">
            <button
              type="button"
              onClick={() => {
                setNoticeOpen(open => {
                  if (!open) loadNotifications();
                  return !open;
                });
              }}
              className="relative text-gray-600 hover:text-nailong-orange font-medium transition-colors text-sm md:text-base whitespace-nowrap"
            >
              通知
              {unreadCount > 0 && (
                <span className="absolute -top-2 -right-3 min-w-[18px] h-[18px] px-1 rounded-full bg-red-400 text-white text-[10px] leading-[18px] text-center">
                  {unreadCount}
                </span>
              )}
            </button>

            {noticeOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl shadow-nailong border border-nailong-cream-dark z-[60] overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-nailong-cream-dark">
                  <span className="font-semibold text-gray-800">通知</span>
                  <div className="flex items-center gap-3">
                    <button type="button" onClick={() => notificationsApi.markAllRead().then(loadNotifications)} className="text-xs text-nailong-orange">全部已读</button>
                    <button type="button" onClick={() => setNoticeOpen(false)} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
                  </div>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.map(n => (
                    <button
                      key={n.id}
                      type="button"
                      onClick={() => void handleNotificationClick(n)}
                      className="w-full text-left px-4 py-3 hover:bg-nailong-cream border-b border-nailong-cream-dark last:border-0"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium text-sm text-gray-800">{n.title}</span>
                        {!n.read_at && <span className="w-2 h-2 bg-nailong-orange rounded-full shrink-0" />}
                      </div>
                      <p className="text-xs text-gray-500 mt-1 leading-5">{n.message}</p>
                    </button>
                  ))}
                  {notifications.length === 0 && <div className="text-center text-gray-400 py-8 text-sm">暂无通知</div>}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 md:gap-4 shrink-0">
            <Link to="/profile" className="text-gray-600 hover:text-nailong-orange font-medium transition-colors text-sm md:text-base whitespace-nowrap">我的</Link>
            <span className="text-gray-600 hidden md:inline max-w-[80px] truncate">{user?.name}</span>
            <button type="button" onClick={() => { logout(); navigate("/login"); }}
                    className="text-xs md:text-sm text-red-400 hover:text-red-500 hover:underline transition-colors whitespace-nowrap">退出</button>
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto p-4 animate-nailong-fade-in">
        <Outlet />
      </main>
      {agentOpen && <AgentPanel onClose={() => setAgentOpen(false)} />}
    </div>
  );
}
