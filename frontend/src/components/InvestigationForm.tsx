import React, { useState } from "react";
import { ArrowUpRight, User, Mail, Phone, Search, Globe, Sparkles } from "lucide-react";
import type { InvestigationRequest, TargetType } from "../types";

interface InvestigationFormProps {
  onSubmit: (payload: InvestigationRequest) => Promise<void>;
  busy: boolean;
}

type TabMode = "unified" | "all" | "username" | "email" | "phone" | "name" | "web";

export function InvestigationForm({ onSubmit, busy }: InvestigationFormProps) {
  const [activeTab, setActiveTab] = useState<TabMode>("unified");
  const [unifiedQuery, setUnifiedQuery] = useState("");
  const [unifiedType, setUnifiedType] = useState<TargetType>("username");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [web, setWeb] = useState("");
  const [enablePivot, setEnablePivot] = useState(false);
  const [localError, setLocalError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: InvestigationRequest = {};

    if (activeTab === "unified") {
      if (!unifiedQuery.trim()) {
        setLocalError("Please enter a search query.");
        return;
      }
      payload.query = unifiedQuery.trim();
      payload.target_type = unifiedType;
      if (unifiedType === "username") payload.username = unifiedQuery.trim();
      else if (unifiedType === "email") payload.email = unifiedQuery.trim();
      else if (unifiedType === "phone") payload.phone = unifiedQuery.trim();
      else if (unifiedType === "name") payload.name = unifiedQuery.trim();
      else if (unifiedType === "web") payload.web = unifiedQuery.trim();
    } else {
      if (username.trim()) payload.username = username.trim();
      if (email.trim()) payload.email = email.trim();
      if (phone.trim()) payload.phone = phone.trim();
      if (name.trim()) payload.name = name.trim();
      if (web.trim()) payload.web = web.trim();
    }

    if (enablePivot) {
      payload.enable_pivot = true;
      payload.max_pivot_depth = 1;
      payload.max_pivot_budget = 5;
    }

    if (!payload.username && !payload.email && !payload.phone && !payload.name && !payload.web && !payload.query) {
      setLocalError("Enter at least one target identifier.");
      return;
    }

    setLocalError("");
    await onSubmit(payload);
  }

  return (
    <section className="panel">
      <div className="sectionTitle">
        <span className="number">01</span>
        <div>
          <h2>OpenTrace OSINT Engine</h2>
          <p>Search public, authorized digital footprints across 140+ verified sources without paid APIs.</p>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={() => setActiveTab("unified")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "unified" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "unified" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          <Sparkles size={12} style={{ display: "inline", marginRight: "4px" }} /> Unified Search
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("all")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "all" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "all" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Multi-Field
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("username")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "username" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "username" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          <User size={12} style={{ display: "inline", marginRight: "4px" }} /> Username
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("email")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "email" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "email" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          <Mail size={12} style={{ display: "inline", marginRight: "4px" }} /> Email
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("phone")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "phone" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "phone" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          <Phone size={12} style={{ display: "inline", marginRight: "4px" }} /> Phone
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("name")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "name" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "name" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          <Search size={12} style={{ display: "inline", marginRight: "4px" }} /> Name / Scholar
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("web")}
          style={{
            padding: "6px 12px",
            fontSize: "12px",
            background: activeTab === "web" ? "#00f0ff" : "#1a1f2c",
            color: activeTab === "web" ? "#0a0c10" : "#8e9bb0",
            border: "1px solid #2d3748",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          <Globe size={12} style={{ display: "inline", marginRight: "4px" }} /> Web Search
        </button>
      </div>

      {localError && (
        <div className="error" role="alert" style={{ marginBottom: "12px" }}>
          {localError}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {activeTab === "unified" && (
          <div>
            <label htmlFor="unifiedQuery">
              Unified Search Query <small>Select query target type and enter query</small>
            </label>
            <div style={{ display: "flex", gap: "8px" }}>
              <select
                value={unifiedType}
                onChange={(e) => setUnifiedType(e.target.value as TargetType)}
                style={{
                  background: "#161b22",
                  color: "#c9d1d9",
                  border: "1px solid #30363d",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  fontSize: "14px",
                  cursor: "pointer",
                  width: "160px",
                }}
              >
                <option value="username">Username (118)</option>
                <option value="email">Email (13)</option>
                <option value="phone">Phone (7)</option>
                <option value="name">Name / Person (9)</option>
                <option value="web">Web Query (2)</option>
              </select>
              <input
                id="unifiedQuery"
                value={unifiedQuery}
                onChange={(e) => setUnifiedQuery(e.target.value)}
                placeholder={
                  unifiedType === "username"
                    ? "e.g. torvalds, octocat"
                    : unifiedType === "email"
                    ? "e.g. user@domain.com"
                    : unifiedType === "phone"
                    ? "e.g. +14155552671"
                    : unifiedType === "name"
                    ? "e.g. Alan Turing, Claude Shannon"
                    : "e.g. open source intelligence security"
                }
                maxLength={150}
                style={{ flex: 1 }}
              />
            </div>
          </div>
        )}

        {(activeTab === "all" || activeTab === "username") && (
          <div>
            <label htmlFor="username">
              Username <small>Public developer, social, and community profiles (118 platforms)</small>
            </label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. torvalds, octocat"
              maxLength={100}
            />
          </div>
        )}

        {(activeTab === "all" || activeTab === "email") && (
          <div>
            <label htmlFor="email">
              Email <small>Syntax, MX DNS, disposable detection, Gravatar, RDAP & CT logs</small>
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. user@domain.com"
              maxLength={254}
            />
          </div>
        )}

        {(activeTab === "all" || activeTab === "phone") && (
          <div>
            <label htmlFor="phone">
              Phone Number <small>E.164 format with country calling code and ITU-T rules</small>
            </label>
            <input
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="e.g. +14155552671"
              maxLength={40}
            />
          </div>
        )}

        {(activeTab === "all" || activeTab === "name") && (
          <div>
            <label htmlFor="name">
              Full Name / Person <small>Wikidata, Wikipedia, DBLP & Semantic Scholar authors</small>
            </label>
            <input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Alan Turing, Claude Shannon"
              maxLength={120}
            />
          </div>
        )}

        {(activeTab === "all" || activeTab === "web") && (
          <div>
            <label htmlFor="web">
              Web Search Query <small>DuckDuckGo instant knowledge and open search metasearch</small>
            </label>
            <input
              id="web"
              value={web}
              onChange={(e) => setWeb(e.target.value)}
              placeholder="e.g. digital footprint investigation platform"
              maxLength={200}
            />
          </div>
        )}

        <div style={{ marginTop: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            id="enablePivot"
            type="checkbox"
            checked={enablePivot}
            onChange={(e) => setEnablePivot(e.target.checked)}
            style={{ width: "auto", margin: 0, cursor: "pointer" }}
          />
          <label htmlFor="enablePivot" style={{ margin: 0, cursor: "pointer", fontSize: "13px", color: "#c9d1d9" }}>
            Enable Recursive Pivoting <small style={{ color: "#8b949e" }}>(Automatically extract discovered emails/usernames and investigate second layer)</small>
          </label>
        </div>

        <button className="primary" disabled={busy} style={{ marginTop: "16px" }}>
          {busy ? "Investigating across sources…" : "Launch Investigation"}{" "}
          <ArrowUpRight size={16} />
        </button>
      </form>

      <p className="disclaimer" style={{ marginTop: "16px" }}>
        Strict compliance: Public sources only. Zero paid APIs required. Strictly no password dumps, private mailbox probing,
        credential stuffing, or CAPTCHA bypass. Matches are candidates, not proof of personal identity.
      </p>
    </section>
  );
}
