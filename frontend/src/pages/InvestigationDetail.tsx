import { ArrowLeft, Download } from "lucide-react";
import { FindingsList } from "../components/FindingsList";
import type { Investigation } from "../types";

interface InvestigationDetailProps {
  investigation: Investigation;
  onBack: () => void;
}

export function InvestigationDetail({
  investigation,
  onBack,
}: InvestigationDetailProps) {
  const exportBase = `/api/v1/investigations/${encodeURIComponent(investigation.id)}/export`;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <button className="ghost" onClick={onBack}>
          <ArrowLeft size={16} /> Back to dashboard
        </button>

        <div style={{ display: "flex", gap: "8px" }}>
          <a className="ghost" href={`${exportBase}?format=json`} download>
            <Download size={14} /> JSON
          </a>
          <a className="ghost" href={`${exportBase}?format=csv`} download>
            <Download size={14} /> CSV
          </a>
          <a className="ghost" href={`${exportBase}?format=html`} download target="_blank" rel="noreferrer">
            <Download size={14} /> HTML
          </a>
        </div>
      </div>

      <div className="panel resultsPanel">
        <div className="sectionTitle">
          <span className="number">RES</span>
          <div>
            <h2>Investigation Findings</h2>
            <p>
              {investigation.findings.length} findings · Status:{" "}
              <strong className={`status ${investigation.status}`}>
                {investigation.status.toUpperCase()}
              </strong>
            </p>
          </div>
        </div>

        <div className="resultMeta">
          <span>ID</span>
          <code>{investigation.id}</code>
          <button
            className="textButton"
            onClick={() => {
              void navigator.clipboard?.writeText(investigation.id);
            }}
          >
            Copy ID
          </button>
        </div>

        {investigation.warnings && investigation.warnings.length > 0 && (
          <div style={{ marginBottom: "14px" }}>
            {investigation.warnings.map((warning, i) => (
              <div className="warning" key={i}>
                {warning}
              </div>
            ))}
          </div>
        )}

        <FindingsList findings={investigation.findings} />
      </div>
    </div>
  );
}
