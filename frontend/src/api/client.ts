import type {
  Investigation,
  InvestigationRequest,
  ManifestSource,
  ModuleInfo,
  PlatformStats,
  TokenResponse,
  User,
} from "../types";

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
export const API_PREFIX = `${API_BASE}/api/v1`;

const TOKEN_KEY = "opentrace_auth_token";

export const authStorage = {
  getToken: (): string | null => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string | null) => {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  },
};


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = authStorage.getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  // Modules and Sources
  modules: () => request<ModuleInfo[]>("/modules"),
  sources: (params?: { status?: string; category?: string; target_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.category) query.set("category", params.category);
    if (params?.target_type) query.set("target_type", params.target_type);
    const qs = query.toString();
    return request<ManifestSource[]>(`/sources${qs ? `?${qs}` : ""}`);
  },
  sourcesHealthSummary: () =>
    request<{
      total_active_sources: number;
      healthy_count: number;
      free_count: number;
      requires_key_count: number;
      sources: Array<Record<string, unknown>>;
    }>("/sources/health/summary"),
  sourceHealth: (sourceId: string) =>
    request<Record<string, unknown>>(`/sources/${encodeURIComponent(sourceId)}/health`),
  stats: () => request<PlatformStats>("/stats"),

  // Investigations
  list: () => request<Investigation[]>("/investigations?limit=50"),
  get: (id: string) => request<Investigation>(`/investigations/${encodeURIComponent(id)}`),
  create: (payload: InvestigationRequest) =>
    request<Investigation>("/investigations", { method: "POST", body: JSON.stringify(payload) }),
  retry: (id: string) =>
    request<Investigation>(`/investigations/${encodeURIComponent(id)}/retry`, { method: "POST" }),
  cancel: (id: string) =>
    request<{ investigation_id: string; cancelled: boolean }>(
      `/investigations/${encodeURIComponent(id)}/cancel`,
      {
        method: "POST",
      }
    ),
  delete: (id: string) =>
    request<{ deleted: boolean }>(`/investigations/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),
  exportInvestigation: async (
    id: string,
    format: "json" | "csv" | "html"
  ): Promise<void> => {
    const token = authStorage.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const response = await fetch(
      `${API_PREFIX}/investigations/${encodeURIComponent(id)}/export?format=${format}`,
      { headers }
    );
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body?.error?.message ?? body?.detail ?? `Export failed (${response.status})`);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `opentrace-${id}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },

  // User Authentication & Account
  auth: {
    register: (payload: { email: string; password: string; name: string }) =>
      request<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    login: (payload: { email: string; password: string }) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    logout: () =>
      request<{ logged_out: boolean }>("/auth/logout", {
        method: "POST",
      }),
    me: () => request<User>("/auth/me"),
    updateProfile: (payload: { name?: string; preferences?: Record<string, unknown> }) =>
      request<User>("/auth/me", {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    changePassword: (payload: { current_password: string; new_password: string }) =>
      request<{ message: string }>("/auth/change-password", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    deleteAccount: () =>
      request<{ deleted: boolean }>("/auth/me", {
        method: "DELETE",
      }),
    forgotPassword: (email: string) =>
      request<{ message: string; reset_token?: string }>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    resetPassword: (payload: { token: string; new_password: string }) =>
      request<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
};
