import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (detail) {
        setError(typeof detail === "string" ? detail : JSON.stringify(detail));
      } else if (err.response?.status === 0 || err.code === "ERR_NETWORK") {
        setError("无法连接到服务器，请确认后端已启动");
      } else if (err.response?.status === 401) {
        setError("用户名或密码错误");
      } else {
        setError(`登录失败 (${err.response?.status || "网络错误"})`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-nailong-cream via-yellow-50 to-nailong-cream-dark">
      <form onSubmit={handleSubmit} className="card-nailong p-8 w-96">
        <div className="text-center mb-8">
          <img src="https://www.nailoong.com/img/ipStar/image_nailoong.png" alt="奶龙" className="w-32 h-32 mx-auto mb-3 animate-nailong-bounce-gentle object-contain" />
          <h1 className="text-2xl font-bold text-gray-800">欢迎回来</h1>
          <p className="text-nailong-orange text-sm mt-1 font-medium">奶龙羽毛球</p>
        </div>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl mb-4 text-sm">
            <div className="font-medium mb-1">登录失败</div>
            <div className="text-red-600">{error}</div>
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">用户名</label>
            <input value={username} onChange={e => setUsername(e.target.value)}
                   placeholder="请输入用户名" className="input-nailong" autoFocus required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">密码</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                   placeholder="请输入密码" className="input-nailong" required />
          </div>
        </div>
        <button type="submit" disabled={loading}
                className="btn-nailong w-full mt-6 disabled:opacity-50 disabled:cursor-not-allowed">
          {loading ? "登录中..." : "登录"}
        </button>
        <p className="text-center mt-6 text-sm text-gray-500">
          还没有账号？<Link to="/register" className="text-nailong-orange font-semibold hover:text-nailong-orange-dark">注册</Link>
        </p>
      </form>
    </div>
  );
}
