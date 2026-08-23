const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_BACKEND_ORIGIN ||
  "http://localhost:8000";
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    ...options,
    headers,
    credentials: "include"
  });

  if (response.status !== 401 || path === "/auth/refresh") {
    return parseResponse(response);
  }

  const refreshed = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include"
  });
  if (!refreshed.ok) {
    accessToken = null;
    return parseResponse(response);
  }
  const payload = await refreshed.json();
  accessToken = payload.access_token;
  headers.set("Authorization", `Bearer ${accessToken}`);

  return parseResponse(
    await fetch(`${API_BASE_URL}/api/v1${path}`, {
      ...options,
      headers,
      credentials: "include"
    })
  );
}

async function parseResponse(response) {
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const message = payload?.error?.message || "Request failed";
    throw new Error(message);
  }
  return payload;
}
