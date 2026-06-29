import { useState, useEffect, createContext, useContext } from "react";
import * as authApi from "../api/auth";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuthProvider(): AuthState {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const u = await authApi.me();
      setUser(u);
    } catch {
      localStorage.removeItem("token");
      setUser(null);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetchUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  return {
    user, loading,
    login: async (username, password) => {
      const res = await authApi.login(username, password);
      localStorage.setItem("token", res.token);
      setUser(res.user);
    },
    register: async (username, password, name) => {
      const res = await authApi.register(username, password, name);
      localStorage.setItem("token", res.token);
      setUser(res.user);
    },
    logout: () => { localStorage.removeItem("token"); setUser(null); },
    refreshUser: fetchUser,
  };
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
