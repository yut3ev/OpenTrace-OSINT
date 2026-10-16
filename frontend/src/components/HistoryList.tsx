import { Trash2 } from "lucide-react";
import type { Investigation } from "../types";

interface HistoryListProps {
  history: Investigation[];
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function HistoryList({ history, onSelect, onDelete }: HistoryListProps) {
  return (
    <section className="panel historyPanel">
      <div className="sectionTitle">
        <span className="number">03</span>
        <div>
          <h2>Recent investigations</h2>
          <p>Stored according to your configured storage mode.</p>
        </div>
      </div>

      {history.length ? (
        <div className="history">
          {history.map((item) => {
            const targetLabel =
              item.request.username ||
              item.request.email ||
              item.request.phone ||
              "Investigation";

            return (
              <div
                key={item.id}
                style={{ display: "flex", gap: "8px", alignItems: "center" }}
              >
                <button
                  className="historyItem"
                  style={{ flex: 1 }}
                  onClick={() => onSelect(item.id)}
                >
                  <span>
                    <strong>{targetLabel}</strong>
                    <small>{new Date(item.created_at).toLocaleString()}</small>
                  </span>
                  <span className={`status ${item.status}`}>{item.status}</span>
                </button>
                {onDelete && (
                  <button
                    className="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(item.id);
                    }}
                    title="Delete investigation"
                    aria-label="Delete investigation"
                    style={{ padding: "10px" }}
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="muted">No investigations saved in this session.</p>
      )}
    </section>
  );
}
