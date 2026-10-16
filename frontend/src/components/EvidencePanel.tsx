import { ShieldCheck } from "lucide-react";
import type { Finding } from "../types";

interface EvidencePanelProps {
  finding: Finding | null;
}

export function EvidencePanel({ finding }: EvidencePanelProps) {
  if (!finding) {
    return (
      <div className="panel empty">
        <ShieldCheck size={32} />
        <strong>Select a finding</strong>
        <span>Select an individual finding to inspect full cryptographic and provenance details.</span>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="sectionTitle">
        <span className="number">EV</span>
        <div>
          <h2>Evidence Provenance</h2>
          <p>{finding.module_id}</p>
        </div>
      </div>

      <div className="resultMeta">
        <span>Observed:</span>
        <code>{new Date(finding.observed_at).toISOString()}</code>
      </div>

      <div className="resultMeta">
        <span>Source:</span>
        <strong>{finding.source_name}</strong>
      </div>

      {finding.source_url && (
        <div className="resultMeta">
          <span>Source URL:</span>
          <code>{finding.source_url}</code>
        </div>
      )}

      <p style={{ marginTop: "12px", lineHeight: "1.6" }}>{finding.evidence}</p>

      {finding.data && Object.keys(finding.data).length > 0 && (
        <pre style={{ marginTop: "12px" }}>
          {JSON.stringify(finding.data, null, 2)}
        </pre>
      )}
    </div>
  );
}
