import { useState } from "react";
import { ArrowLeft, Clock, Download, XCircle } from "lucide-react";
import { FindingsList } from "../components/FindingsList";
import { api } from "../api/client";
import type { Investigation } from "../types";

interface InvestigationDetailProps {
  investigation: Investigation;
  onBack: () => void;
}

export function InvestigationDetail({
  investigation,
  onBack,
}: InvestigationDetailProps) {
  const [cancelling, setCancelling] = useState(false);
  const [cancelledLocally, setCancelledLocally] = useState(false);
  const exportBase = `/api/v1/investigations/${encodeURIComponent(investigation.id)}/export`;

  async function handleCancel() {
    setCancelling(true);
    try {
      await api.cancel(investigation.id);
      setCancelledLocally(true);
    } catch (e) {
      console.error("Cancel failed:", e);
    } finally {
      setCancelling(false);
    }
  }

  const metrics = investigation.summary?.metrics;
  const currentStatus = cancelledLocally ? "cancelled" : investigation.status;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <button className="ghost" onClick={onBack}>
          <ArrowLeft size={16} /> Back to dashboard
        </button>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {(currentStatus === "running" || currentStatus === "queued") && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              style={{
                background: "#b91c1c",
                color: "#fff",
                border: "none",
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "12px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <XCircle size={14} /> {cancelling ? "Cancelling…" : "Cancel Search"}
            </button>
          )}

          <a className="ghost" href={`${exportBase}?format=json`} download>
            <Download size={14} /> JSON
          </a>
          <a className="ghost" href={`${exportBase}?format=csv`} download>
            <Download size={14} /> CSV
          </a>
          <a
            className="ghost"
            href={`${exportBase}?format=html`}
            download
            target="_blank"
            rel="noreferrer"
          >
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
              <strong className={`status ${currentStatus}`}>
                {currentStatus.toUpperCase()}
              </strong>
              {investigation.summary?.duration_seconds !== undefined && (
                <span style={{ marginLeft: "10px", color: "#8b949e" }}>
                  <Clock size={12} style={{ display: "inline", marginRight: "3px" }} />
                  {investigation.summary.duration_seconds}s
                </span>
              )}
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

        {metrics && (
          <div
            style={{
              background: "#0d1117",
              border: "1px solid #30363d",
              borderRadius: "6px",
              padding: "10px 14px",
              margin: "12px 0",
              fontSize: "12px",
              display: "flex",
              gap: "16px",
              flexWrap: "wrap",
            }}
          >
            <div>
              <span style={{ color: "#8b949e" }}>Registered Sources: </span>
              <strong>{metrics.registered}</strong>
            </div>
            <div>
              <span style={{ color: "#8b949e" }}>Eligible: </span>
              <strong>{metrics.eligible}</strong>
            </div>
            <div>
              <span style={{ color: "#8b949e" }}>Attempted: </span>
              <strong style={{ color: "#58a6ff" }}>{metrics.attempted}</strong>
            </div>
            <div>
              <span style={{ color: "#8b949e" }}>Succeeded: </span>
              <strong style={{ color: "#3fb950" }}>{metrics.succeeded}</strong>
            </div>
            <div>
              <span style={{ color: "#8b949e" }}>No Match: </span>
              <strong style={{ color: "#8b949e" }}>{metrics.no_match}</strong>
            </div>
            {metrics.rate_limited > 0 && (
              <div>
                <span style={{ color: "#8b949e" }}>Rate Limited: </span>
                <strong style={{ color: "#d29922" }}>{metrics.rate_limited}</strong>
              </div>
            )}
            {metrics.blocked > 0 && (
              <div>
                <span style={{ color: "#8b949e" }}>Blocked: </span>
                <strong style={{ color: "#f85149" }}>{metrics.blocked}</strong>
              </div>
            )}
            {metrics.error > 0 && (
              <div>
                <span style={{ color: "#8b949e" }}>Errors: </span>
                <strong style={{ color: "#f85149" }}>{metrics.error}</strong>
              </div>
            )}
          </div>
        )}

        {(investigation.cancellation_reason || cancelledLocally) && (
          <div className="warning" style={{ marginBottom: "14px" }}>
            Investigation was cancelled:{" "}
            {investigation.cancellation_reason || "Cancelled by user request."}
          </div>
        )}

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
