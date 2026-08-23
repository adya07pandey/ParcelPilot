import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch, setAccessToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function restoreSession() {
      try {
        const payload = await apiFetch("/auth/refresh", { method: "POST" });
        if (!active) return;
        setAccessToken(payload.access_token);
        setUser(payload.user);
      } catch {
        if (!active) return;
        setAccessToken(null);
        setUser(null);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    restoreSession();
    return () => {
      active = false;
    };
  }, []);

  async function login(email, password) {
    setLoading(true);
    try {
      const payload = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      setAccessToken(payload.access_token);
      setUser(payload.user);
      return payload.user;
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" }).catch(() => null);
    setAccessToken(null);
    setUser(null);
  }

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
