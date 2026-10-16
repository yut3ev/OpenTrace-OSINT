export type TargetType = "username" | "email" | "phone" | "name";
export type FindingStatus = "found" | "not_found" | "unknown" | "info" | "error";
export type SourceStatus =
  | "registered"
  | "queued"
  | "running"
  | "succeeded"
  | "no_match"
  | "rate_limited"
  | "blocked"
  | "unavailable"
  | "error"
  | "skipped";

export interface InvestigationRequest {
  username?: string;
  email?: string;
  phone?: string;
  name?: string;
  modules?: string[];
  max_runtime_seconds?: number;
}

export interface Finding {
  id: string;
  module_id: string;
  source_id?: string;
  target_type: TargetType;
  search_type?: string;
  matched_identifier?: string;
  status: FindingStatus;
  source_status?: SourceStatus;
  verification_status?: "verified" | "unverified" | "ambiguous" | "candidate";
  title: string;
  evidence: string;
  source_name: string;
  source_url?: string;
  profile_url?: string;
  public_evidence_url?: string;
  observed_at: string;
  confidence: "none" | "low" | "medium" | "high";
  confidence_reasons?: string[];
  limitations?: string[];
  data: Record<string, unknown>;
}

export interface SourceMetrics {
  registered: number;
  eligible: number;
  attempted: number;
  succeeded: number;
  no_match: number;
  rate_limited: number;
  blocked: number;
  unavailable: number;
  error: number;
  skipped: number;
}

export interface Investigation {
  id: string;
  status: "queued" | "running" | "completed" | "partial" | "failed" | "cancelled";
  created_at: string;
  completed_at?: string;
  request: InvestigationRequest;
  findings: Finding[];
  summary: {
    total: number;
    by_status: Record<string, number>;
    duration_seconds?: number;
    module_statuses?: Record<string, string>;
    metrics?: SourceMetrics;
  };
  warnings: string[];
  cancellation_reason?: string;
}

export interface ModuleInfo {
  id: string;
  name: string;
  version: string;
  supported_targets: TargetType[];
  enabled: boolean;
  implementation_status: "implemented" | "planned" | "disabled" | string;
  source: string;
  limitations: string[];
}

export interface ManifestSource {
  id: string;
  name: string;
  category: string;
  target_type: string;
  access_type: string;
  source_url: string;
  status: string;
  capabilities: string[];
  description: string;
  limitations: string[];
  api_url?: string;
  is_active: boolean;
}

export interface PlatformStats {
  total_investigations: number;
  total_findings: number;
  total_manifest_sources: number;
  total_active_modules: number;
  sources_by_status: Record<string, number>;
  sources_by_category: Record<string, number>;
  sources_by_target: Record<string, number>;
}
