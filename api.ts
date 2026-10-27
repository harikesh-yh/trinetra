// Thin client for the TRINETRA engine. In dev, Vite proxies /api -> :8077.
const BASE = "/api";

export interface UserInfo {
  username: string;
  role: string;
  scope: string;
}

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export const api = {
  users: () => getJSON<UserInfo[]>("/users"),
  login: (username: string) => postJSON<UserInfo>("/login", { username }),
  ask: (username: string, question: string) =>
    postJSON<any>("/ask", { username, question }),
  hotspots: (username: string, crime?: string, days = 90) =>
    getJSON<any>(
      `/hotspots?username=${username}&days=${days}` +
        (crime ? `&crime=${encodeURIComponent(crime)}` : "")
    ),
  forecast: (username: string, crime?: string) =>
    getJSON<any>(
      `/forecast?username=${username}` +
        (crime ? `&crime=${encodeURIComponent(crime)}` : "")
    ),
  graph: (username: string) => getJSON<any>(`/graph?username=${username}`),
  anomalies: (username: string) => getJSON<any>(`/anomalies?username=${username}`),
  risk: (username: string) => getJSON<any>(`/risk?username=${username}`),
  detection: (username: string) =>
    getJSON<any>(`/detection-quality?username=${username}`),
  responseLag: (username: string) =>
    getJSON<any>(`/response-lag?username=${username}`),
  socio: (username: string, crime?: string, dimension = "occupation") =>
    getJSON<any>(
      `/socioeconomic?username=${username}&dimension=${dimension}` +
        (crime ? `&crime=${encodeURIComponent(crime)}` : "")
    ),
  audit: (username: string, limit = 50) =>
    getJSON<any>(`/audit?username=${username}&limit=${limit}`),
  briefUrl: () => `${BASE}/brief.pdf`,
};
