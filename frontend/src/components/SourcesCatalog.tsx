import { useEffect, useState } from "react";
import { CheckCircle2, Globe, KeyRound, Lock, Search } from "lucide-react";
import { api } from "../api/client";
import type { ManifestSource } from "../types";

export function SourcesCatalog() {
  const [sources, setSources] = useState<ManifestSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterText, setFilterText] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    void api
      .sources()
      .then((data) => {
        setSources(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const categories = Array.from(new Set(sources.map((s) => s.category)));

  const filtered = sources.filter((s) => {
    const matchesText =
      s.name.toLowerCase().includes(filterText.toLowerCase()) ||
      s.id.toLowerCase().includes(filterText.toLowerCase()) ||
      s.description.toLowerCase().includes(filterText.toLowerCase());
    const matchesCategory = categoryFilter === "all" || s.category === categoryFilter;
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && s.is_active) ||
      (statusFilter === "implemented" && s.status === "implemented") ||
      (statusFilter === "planned" && s.status === "planned") ||
      (statusFilter === "requires_api_key" && s.status === "requires_api_key");

    return matchesText && matchesCategory && matchesStatus;
  });

  return (
    <div className="panel" style={{ marginTop: "18px" }}>
      <div className="sectionTitle">
        <span className="number">SRC</span>
        <div>
          <h2>Public Source Registry & Coverage Catalog</h2>
          <p>
            {sources.length} cataloged sources · Transparently separating operational adapters from
            planned roadmap sources.
          </p>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: "10px",
          marginBottom: "16px",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <div style={{ position: "relative", flex: 1, minWidth: "200px" }}>
          <Search
            size={14}
            style={{
              position: "absolute",
              left: "10px",
              top: "50%",
              transform: "translateY(-50%)",
              color: "#6b7280",
            }}
          />
          <input
            type="text"
            placeholder="Search sources by name or ID..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{ paddingLeft: "32px", width: "100%", margin: 0 }}
          />
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          style={{
            padding: "8px 12px",
            background: "#161b22",
            color: "#e6edf3",
            border: "1px solid #30363d",
            borderRadius: "6px",
          }}
        >
          <option value="all">All Categories ({categories.length})</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c.toUpperCase()}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: "8px 12px",
            background: "#161b22",
            color: "#e6edf3",
            border: "1px solid #30363d",
            borderRadius: "6px",
          }}
        >
          <option value="all">All Statuses</option>
          <option value="active">Active & Running ({sources.filter((s) => s.is_active).length})</option>
          <option value="implemented">Implemented</option>
          <option value="requires_api_key">Requires API Key</option>
          <option value="planned">Planned</option>
        </select>
      </div>

      {loading ? (
        <div style={{ padding: "20px", textAlign: "center", color: "#8b949e" }}>
          Loading source catalog...
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "12px",
          }}
        >
          {filtered.map((s) => {
            const statusBg =
              s.is_active || s.status === "implemented"
                ? "#0e4429"
                : s.status === "requires_api_key"
                ? "#4d3800"
                : "#21262d";
            const statusColor =
              s.is_active || s.status === "implemented"
                ? "#3fb950"
                : s.status === "requires_api_key"
                ? "#d29922"
                : "#8b949e";

            return (
              <div
                key={s.id}
                style={{
                  background: "#0d1117",
                  border: "1px solid #30363d",
                  borderRadius: "8px",
                  padding: "14px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "6px",
                    }}
                  >
                    <div>
                      <span
                        style={{
                          fontSize: "11px",
                          fontFamily: "monospace",
                          color: "#58a6ff",
                          textTransform: "uppercase",
                        }}
                      >
                        {s.category} · {s.target_type}
                      </span>
                      <h4 style={{ margin: "2px 0 0 0", fontSize: "14px", fontWeight: "600" }}>
                        {s.name}
                      </h4>
                    </div>

                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "12px",
                        fontSize: "10px",
                        fontWeight: "600",
                        background: statusBg,
                        color: statusColor,
                      }}
                    >
                      {s.is_active ? "ACTIVE" : s.status.toUpperCase()}
                    </span>
                  </div>

                  <p
                    style={{
                      fontSize: "12px",
                      color: "#8b949e",
                      margin: "6px 0 10px 0",
                      lineHeight: "1.4",
                    }}
                  >
                    {s.description || "No description provided."}
                  </p>
                </div>

                <div
                  style={{
                    borderTop: "1px solid #21262d",
                    paddingTop: "8px",
                    fontSize: "11px",
                    color: "#8b949e",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    {s.access_type === "requires_api_key" ? (
                      <KeyRound size={12} color="#d29922" />
                    ) : s.access_type === "public_api" ? (
                      <Globe size={12} color="#58a6ff" />
                    ) : (
                      <Lock size={12} color="#8b949e" />
                    )}
                    {s.access_type}
                  </span>

                  {s.is_active && (
                    <span
                      style={{
                        color: "#3fb950",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontWeight: "500",
                      }}
                    >
                      <CheckCircle2 size={12} /> Ready
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
