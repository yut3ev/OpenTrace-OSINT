import type { Investigation, InvestigationRequest, ModuleInfo } from "../types";

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
  list: () => request<Investigation[]>("/investigations?limit=20"),
  get: (id: string) => request<Investigation>(`/investigations/${encodeURIComponent(id)}`),
  create: (payload: InvestigationRequest) =>
    request<Investigation>("/investigations", { method: "POST", body: JSON.stringify(payload) }),
  delete: (id: string) =>
    request<{ deleted: boolean }>(`/investigations/${encodeURIComponent(id)}`, { method: "DELETE" }),
};
