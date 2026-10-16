import type {
  Investigation,
  InvestigationRequest,
  ManifestSource,
  ModuleInfo,
  PlatformStats,
} from "../types";

const base = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  modules: () => request<ModuleInfo[]>("/modules"),
  sources: (params?: { status?: string; category?: string; target_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.category) query.set("category", params.category);
    if (params?.target_type) query.set("target_type", params.target_type);
    const qs = query.toString();
    return request<ManifestSource[]>(`/sources${qs ? `?${qs}` : ""}`);
  },
  stats: () => request<PlatformStats>("/stats"),
  list: () => request<Investigation[]>("/investigations?limit=20"),
  get: (id: string) => request<Investigation>(`/investigations/${encodeURIComponent(id)}`),
  create: (payload: InvestigationRequest) =>
    request<Investigation>("/investigations", { method: "POST", body: JSON.stringify(payload) }),
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
};
