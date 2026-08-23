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
        setUser(normalizeAuthUser(payload.user, payload.access_token));
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
      const authUser = normalizeAuthUser(payload.user, payload.access_token);
      setUser(authUser);
      return authUser;
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

function normalizeAuthUser(user, accessToken) {
  const tokenPayload = decodeJwtPayload(accessToken);
  return {
    ...user,
    role: String(user?.role || tokenPayload?.role || "").toUpperCase(),
    account_id: user?.account_id ?? tokenPayload?.account_id ?? null
  };
}

function decodeJwtPayload(token) {
  if (!token) return null;
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(normalized));
  } catch {
    return null;
  }
}
