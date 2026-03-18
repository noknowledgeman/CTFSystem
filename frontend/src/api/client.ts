import type {
  Challenge,
  Hint,
  Submission,
  LeaderboardEntry,
  EventStats,
  TokenResponse,
  User,
  ProgressDetailed,
  ValidationResult,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE;

const TOKEN_KEY = 'ctf_token';
const USER_KEY = 'ctf_user';

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function parseJsonResponse(res: Response) {
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const text = await res.text().catch(() => "");
    const preview = text ? text.slice(0, 200).replace(/\s+/g, " ") : "";
    throw new Error(`Expected JSON but got ${contentType || "unknown"}. ${preview ? `Response preview: ${preview}` : ""}`);
  }
  return res.json();
}

type ApiErrorPayload = { detail?: string; message?: string };

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const apiBase = API_BASE || "/api";
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token)
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      if ((res.headers.get("content-type") || "").includes("application/json")) {
        const err = (await res.json()) as unknown;
        // FastAPI typically returns: { "detail": "..." }
        const payload = err as ApiErrorPayload;
        detail = payload.detail || payload.message || detail;
      } else {
        const text = await res.text().catch(() => "");
        if (text) detail = text.slice(0, 300);
      }
    } catch {
      // Keep statusText as fallback
    }

    // If the backend says the token is invalid, clear local storage so the user
    // can log in again without having to manually refresh localStorage entries.
    if (res.status === 401) {
      const d = String(detail || '').toLowerCase();
      if (d.includes('invalid token') || d.includes('not authenticated') || d.includes('unauthorized')) {
        clearAuth();
      }
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return parseJsonResponse(res);
}

// Auth
export const auth = {
  login: (username: string, password: string) =>
    api<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  register: (username: string, email: string, password: string) =>
    api<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    }),
};

// Challenges
export const challenges = {
  list: () => api<Challenge[]>("/challenges"),
  get: (id: number) => api<Challenge>(`/challenges/${id}`),
  create: (data: Record<string, unknown>) =>
    api<Challenge>("/challenges", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Record<string, unknown>) =>
    api<Challenge>(`/challenges/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: number) => api<void>(`/challenges/${id}`, { method: "DELETE" }),
};

// Hints
export const hints = {
  list: (challengeId: number) => api<Hint[]>(`/hints/challenge/${challengeId}`),
  unlockNext: (challengeId: number) =>
    api<Hint>(`/hints/challenge/${challengeId}/unlock`, { method: "POST" }),
  create: (data: {
    challenge_id: number;
    order: number;
    content: string;
    cost?: number;
  }) => api<Hint>("/hints", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Record<string, unknown>) =>
    api<Hint>(`/hints/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: number) => api<void>(`/hints/${id}`, { method: "DELETE" }),
};

// Submissions
export const submissions = {
  submit: (challenge_id: number, flag: string, description?: string) =>
    api<Submission>("/submissions", {
      method: "POST",
      body: JSON.stringify({ challenge_id, flag, description }),
    }),
  my: () => api<Submission[]>("/submissions"),
  all: (params?: {
    challenge_id?: number;
    user_id?: number;
    team_id?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params?.challenge_id != null)
      sp.set("challenge_id", String(params.challenge_id));
    if (params?.user_id != null) sp.set("user_id", String(params.user_id));
    if (params?.team_id != null) sp.set("team_id", String(params.team_id));
    const q = sp.toString();
    return api<Submission[]>(`/submissions/all${q ? `?${q}` : ""}`);
  },
  grade: (
    id: number,
    data: { status: string; assigned_points?: number; feedback?: string },
  ) =>
    api<Submission>(`/submissions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};

// Leaderboard
export const leaderboard = {
  get: (by: "user" | "team" = "user") =>
    api<LeaderboardEntry[]>(`/leaderboard?by=${by}`),
  myProgress: () =>
    api<{ total_points: number; solved_count: number; username: string }>(
      "/leaderboard/me",
    ),
  myProgressDetailed: () => api<ProgressDetailed>("/leaderboard/me/detailed"),
};

// Teams (player)
export const teams = {
  list: () => api<TeamRead[]>("/teams"),
  join: (teamId: number) =>
    api<{ team: TeamRead; user: User }>(`/teams/${teamId}/join`, {
      method: "POST",
    }),
  leave: () => api<{ user: User }>("/teams/leave", { method: "POST" }),
};

// Admin
export const admin = {
  users: () => api<User[]>("/admin/users"),
  updateUser: (userId: number, data: { is_active?: boolean }) =>
    api<User>(`/admin/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  getChallengeHints: (challengeId: number) =>
    api<Hint[]>(`/admin/challenges/${challengeId}/hints`),
  teams: () => api<TeamRead[]>("/admin/teams"),
  createTeam: (name: string) =>
    api<TeamRead>("/admin/teams", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  stats: () => api<EventStats>("/admin/stats"),
  uploadVmConfig: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const apiBase = API_BASE || "/api";
    return fetch(`${apiBase}/admin/vm-config`, {
      method: "POST",
      headers: { Authorization: `Bearer ${getToken()}` },
      body: form,
    }).then(async (r) => {
      if (!r.ok) {
        let detail = r.statusText;
        try {
          if ((r.headers.get("content-type") || "").includes("application/json")) {
            const e = (await r.json()) as unknown;
            const payload = e as ApiErrorPayload;
            detail = payload.detail || payload.message || detail;
          } else {
            const text = await r.text().catch(() => "");
            if (text) detail = text.slice(0, 300);
          }
        } catch {
          // keep statusText fallback
        }
        throw new Error(detail);
      }
      return parseJsonResponse(r);
    });
  },
  validateChallenges: () =>
    api<ValidationResult[]>("/admin/challenges/validate", { method: "POST" }),
};

export interface TeamRead {
  id: number;
  name: string;
  created_at: string;
}
