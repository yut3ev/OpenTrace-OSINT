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
          <h2>Configure Target</h2>
          <p>Select target vector, input identifiers, and toggle correlation pivoting.</p>
        </div>
      </div>

      <div className="form-tab-nav">
        <button
          type="button"
          onClick={() => setActiveTab("unified")}
          className={`form-tab-btn ${activeTab === "unified" ? "active" : ""}`}
        >
          <Sparkles size={13} /> Unified Search
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("all")}
          className={`form-tab-btn ${activeTab === "all" ? "active" : ""}`}
        >
          Multi-Field
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("username")}
          className={`form-tab-btn ${activeTab === "username" ? "active" : ""}`}
        >
          <User size={13} /> Username
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("email")}
          className={`form-tab-btn ${activeTab === "email" ? "active" : ""}`}
        >
          <Mail size={13} /> Email
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("phone")}
          className={`form-tab-btn ${activeTab === "phone" ? "active" : ""}`}
        >
          <Phone size={13} /> Phone
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("name")}
          className={`form-tab-btn ${activeTab === "name" ? "active" : ""}`}
        >
          <Search size={13} /> Name / Scholar
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("web")}
          className={`form-tab-btn ${activeTab === "web" ? "active" : ""}`}
        >
          <Globe size={13} /> Web Search
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
