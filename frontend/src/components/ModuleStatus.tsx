import type { ModuleInfo } from "../types";

interface ModuleStatusProps {
  modules: ModuleInfo[];
}

export function ModuleStatus({ modules }: ModuleStatusProps) {
  return (
    <div className="panel" style={{ marginTop: "18px" }}>
      <div className="sectionTitle">
        <span className="number">MOD</span>
        <div>
          <h2>Available OSINT Modules</h2>
          <p>Transparent public modules verified by test coverage.</p>
        </div>
      </div>

      <div style={{ display: "grid", gap: "10px" }}>
        {modules.map((mod) => (
          <div key={mod.id} className="finding" style={{ padding: "12px" }}>
            <div className="findingTop">
              <div>
                <span className="eyebrow">{mod.id} v{mod.version}</span>
                <h3>{mod.name}</h3>
              </div>
              <span className={`status ${mod.enabled ? "found" : "error"}`}>
                {mod.implementation_status}
              </span>
            </div>
            <div className="meta" style={{ marginTop: "6px" }}>
              Targets: {mod.supported_targets.join(", ")} · Source: {mod.source}
            </div>
            {mod.limitations && mod.limitations.length > 0 && (
              <details style={{ marginTop: "6px" }}>
                <summary>Known limitations & boundaries</summary>
                <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                  {mod.limitations.map((lim, idx) => (
                    <li key={idx} style={{ fontSize: "11px", color: "var(--muted)" }}>
                      {lim}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
