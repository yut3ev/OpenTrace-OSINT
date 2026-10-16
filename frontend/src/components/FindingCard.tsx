import { ArrowUpRight } from "lucide-react";
import type { Finding } from "../types";

interface FindingCardProps {
  finding: Finding;
}

export function FindingCard({ finding }: FindingCardProps) {
  return (
    <article className="finding">
      <div className="findingTop">
        <div>
          <span className="eyebrow">{finding.module_id}</span>
          <h3>{finding.title}</h3>
        </div>
        <span className={`status ${finding.status}`}>
          {finding.status.replace("_", " ")}
        </span>
      </div>

      <p>{finding.evidence}</p>

      <div className="meta">
        Confidence: {finding.confidence} · {new Date(finding.observed_at).toLocaleString()}
      </div>

      {finding.source_url && (
        <a
          className="source"
          href={finding.source_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Open source <ArrowUpRight size={14} />
        </a>
      )}

      {finding.data && Object.keys(finding.data).length > 0 && (
        <details>
          <summary>Evidence data</summary>
          <pre>{JSON.stringify(finding.data, null, 2)}</pre>
        </details>
      )}
    </article>
  );
}
