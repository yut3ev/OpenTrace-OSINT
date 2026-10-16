import { Activity, Fingerprint, ShieldCheck } from "lucide-react";
import { FindingsList } from "../components/FindingsList";
import { HistoryList } from "../components/HistoryList";
import { InvestigationForm } from "../components/InvestigationForm";
import { ModuleStatus } from "../components/ModuleStatus";
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
  const enabledCount = modules.filter(
    (m) => m.implementation_status === "implemented" && m.enabled
  ).length;

  return (
    <>
      <section className="hero">
        <div>
          <span className="overline">
            <ShieldCheck size={15} /> EVIDENCE FIRST · PRIVACY AWARE
          </span>
          <h2>
            Investigate signals.<br />
            <em>Preserve the evidence.</em>
          </h2>
          <p>
            Run transparent checks against configured public sources. A result is a lead,
            not proof of identity.
          </p>
        </div>
        <div className="heroStat">
          <Activity size={22} />
          <strong>{enabledCount}</strong>
          <span>enabled modules</span>
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
                  ? `${current.findings.length} findings · ${current.status}`
                  : "Your evidence will appear here."}
              </p>
            </div>
          </div>

          {current ? (
            <>
              <div className="resultMeta">
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

              {current.warnings.map((warning, i) => (
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

      <ModuleStatus modules={modules} />
    </>
  );
}
