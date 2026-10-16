export type TargetType = "username" | "email" | "phone";
export type FindingStatus = "found" | "not_found" | "unknown" | "info" | "error";

export interface InvestigationRequest {
  username?: string;
  email?: string;
  phone?: string;
  modules?: string[];
  max_runtime_seconds?: number;
}

export interface Finding {
  id: string;
  module_id: string;
  target_type: TargetType;
  status: FindingStatus;
  title: string;
  evidence: string;
  source_name: string;
  source_url?: string;
  observed_at: string;
  confidence: "none" | "low" | "medium" | "high";
  data: Record<string, unknown>;
}

export interface Investigation {
  id: string;
  status: "queued" | "running" | "completed" | "partial" | "failed" | "cancelled";
  created_at: string;
  request: InvestigationRequest;
  findings: Finding[];
  summary: { total: number; by_status: Record<string, number> };
  warnings: string[];
}

export interface ModuleInfo {
  id: string;
  name: string;
  version: string;
  supported_targets: TargetType[];
  enabled: boolean;
  implementation_status: "implemented" | "planned" | "disabled";
  source: string;
  limitations: string[];
}
