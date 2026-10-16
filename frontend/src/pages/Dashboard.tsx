import { useState } from "react";
import { Activity, Database, Fingerprint, ShieldCheck, XCircle } from "lucide-react";
import { FindingsList } from "../components/FindingsList";
import { HistoryList } from "../components/HistoryList";
import { InvestigationForm } from "../components/InvestigationForm";
import { ModuleStatus } from "../components/ModuleStatus";
import { SourcesCatalog } from "../components/SourcesCatalog";
import { api } from "../api/client";
import type { Investigation, InvestigationRequest, ModuleInfo } from "../types";

interface DashboardProps {
  current: Investigation | null;
  history: Investigation[];
  modules: ModuleInfo[];
  busy: boolean;
  onSubmit: (payload: InvestigationRequest) => Promise<void>;
  onSelectHistory: (id: string) => void;
  onDeleteHistory: (id: string) => void;
}

export function Dashboard({
  current,
  history,
  modules,
  busy,
  onSubmit,
  onSelectHistory,
  onDeleteHistory,
}: DashboardProps) {
  const [activeCatalogTab, setActiveCatalogTab] = useState<"modules" | "catalog">("modules");
  const [cancelling, setCancelling] = useState(false);

  const enabledCount = modules.filter(
    (m) => m.implementation_status === "implemented" && m.enabled
  ).length;

  async function handleCancel() {
    if (!current) return;
    setCancelling(true);
    try {
      await api.cancel(current.id);
    } catch (e) {
      console.error("Cancel failed:", e);
    } finally {
      setCancelling(false);
    }
  }

  const metrics = current?.summary?.metrics;

  return (
    <>
      <section className="console-hero-banner">
        <div className="console-banner-content">
          <div className="console-overline">
            <ShieldCheck size={14} className="text-cyan" />
            <span>OPERATIONAL RECONNAISSANCE CONSOLE · EVIDENCE FIRST</span>
          </div>
          <h2>
            Investigate signals. <em>Preserve the evidence.</em>
          </h2>
          <p>
            Run bounded asynchronous queries across {enabledCount || 149} verified public sources.
            Findings represent corroborated public indicators for investigation leads.
          </p>
        </div>
        <div className="console-stat-box">
          <div className="console-stat-header">
            <Activity size={20} className="text-emerald" />
            <span className="live-pulse"></span>
          </div>
          <strong>{enabledCount || 149}</strong>
          <span>operational modules</span>
        </div>
      </section>

      <div className="layout">
        <InvestigationForm onSubmit={onSubmit} busy={busy} />

        <section className="panel resultsPanel">
          <div className="sectionTitle">
            <span className="number">02</span>
            <div>
              <h2>{current ? "Current findings" : "Results"}</h2>
              <p>
                {current
                  ? `${current.findings.length} findings · ${current.status.toUpperCase()}`
                  : "Your evidence will appear here."}
              </p>
            </div>
          </div>

          {current ? (
            <>
              <div
                className="resultMeta"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span>ID</span>
                  <code>{current.id}</code>
                  <button
                    className="textButton"
                    onClick={() => {
                      void navigator.clipboard?.writeText(current.id);
                    }}
                  >
                    Copy ID
                  </button>
                </div>

                {(current.status === "running" || current.status === "queued") && (
                  <button
                    onClick={handleCancel}
                    disabled={cancelling}
                    style={{
                      background: "#b91c1c",
                      color: "#fff",
                      border: "none",
                      padding: "4px 10px",
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
              </div>

              {metrics && (
                <div
                  style={{
                    background: "#0d1117",
                    border: "1px solid #30363d",
                    borderRadius: "6px",
                    padding: "10px 14px",
                    margin: "10px 0",
                    fontSize: "12px",
                    display: "flex",
                    gap: "16px",
                    flexWrap: "wrap",
                  }}
                >
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

              {current.warnings && current.warnings.map((warning, i) => (
                <div className="warning" key={i}>
                  {warning}
                </div>
              ))}

              <FindingsList findings={current.findings} />
            </>
          ) : (
            <div className="empty">
              <Fingerprint size={36} />
              <strong>Ready when you are</strong>
              <span>Submit an identifier to start a transparent investigation.</span>
            </div>
          )}
        </section>
      </div>

      <HistoryList
        history={history}
        onSelect={onSelectHistory}
        onDelete={onDeleteHistory}
      />

      <div style={{ marginTop: "24px" }}>
        <div style={{ display: "flex", gap: "10px", marginBottom: "12px" }}>
          <button
            type="button"
            onClick={() => setActiveCatalogTab("modules")}
            style={{
              padding: "8px 16px",
              background: activeCatalogTab === "modules" ? "#00f0ff" : "#161b22",
              color: activeCatalogTab === "modules" ? "#0a0c10" : "#8b949e",
              border: "1px solid #30363d",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "600",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Activity size={14} /> Operational Modules ({modules.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveCatalogTab("catalog")}
            style={{
              padding: "8px 16px",
              background: activeCatalogTab === "catalog" ? "#00f0ff" : "#161b22",
              color: activeCatalogTab === "catalog" ? "#0a0c10" : "#8b949e",
              border: "1px solid #30363d",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "600",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Database size={14} /> Full Source Registry (50+)
          </button>
        </div>

        {activeCatalogTab === "modules" ? (
          <ModuleStatus modules={modules} />
        ) : (
          <SourcesCatalog />
        )}
      </div>
    </>
  );
}
