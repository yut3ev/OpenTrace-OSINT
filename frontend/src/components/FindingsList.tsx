import { useState } from "react";
import { FindingCard } from "./FindingCard";
import type { Finding } from "../types";

interface FindingsListProps {
  findings: Finding[];
}

export function FindingsList({ findings }: FindingsListProps) {
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const filtered = filterStatus === "all"
    ? findings
    : findings.filter((f) => f.status === filterStatus);

  const statuses = Array.from(new Set(findings.map((f) => f.status)));

  return (
    <div className="findingsContainer">
      {findings.length > 0 && (
        <div style={{ display: "flex", gap: "8px", marginBottom: "14px", flexWrap: "wrap" }}>
          <button
            className={`textButton ${filterStatus === "all" ? "active" : ""}`}
            onClick={() => setFilterStatus("all")}
          >
            All ({findings.length})
          </button>
          {statuses.map((st) => (
            <button
              key={st}
              className={`textButton ${filterStatus === st ? "active" : ""}`}
              onClick={() => setFilterStatus(st)}
            >
              {st} ({findings.filter((f) => f.status === st).length})
            </button>
          ))}
        </div>
      )}

      <div className="findings">
        {filtered.length ? (
          filtered.map((finding) => (
            <FindingCard key={finding.id} finding={finding} />
          ))
        ) : (
          <div className="empty">
            <span>No findings match the selected status filter.</span>
          </div>
        )}
      </div>
    </div>
  );
}
