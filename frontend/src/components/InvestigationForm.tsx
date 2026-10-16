import React, { useState } from "react";
import { ArrowUpRight, User, Mail, Phone, Search } from "lucide-react";
import type { InvestigationRequest } from "../types";

interface InvestigationFormProps {
  onSubmit: (payload: InvestigationRequest) => Promise<void>;
  busy: boolean;
}

type TabMode = "all" | "username" | "email" | "phone" | "name";

export function InvestigationForm({ onSubmit, busy }: InvestigationFormProps) {
  const [activeTab, setActiveTab] = useState<TabMode>("all");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [localError, setLocalError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: InvestigationRequest = {};
    if (username.trim()) payload.username = username.trim();
    if (email.trim()) payload.email = email.trim();
    if (phone.trim()) payload.phone = phone.trim();
    if (name.trim()) payload.name = name.trim();

    if (!Object.keys(payload).length) {
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
          <h2>New Investigation</h2>
          <p>Search public, authorized digital footprints across 25+ verified sources.</p>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" }}>
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
          All Fields
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
          <Search size={12} style={{ display: "inline", marginRight: "4px" }} /> Name / People
        </button>
      </div>

      {localError && (
        <div className="error" role="alert" style={{ marginBottom: "12px" }}>
          {localError}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {(activeTab === "all" || activeTab === "username") && (
          <div>
            <label htmlFor="username">
              Username <small>Public developer, social, and community profiles</small>
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
              Email <small>Syntax, MX DNS, disposable detection & Gravatar</small>
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
              Phone Number <small>E.164 format with country calling code</small>
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
              Full Name / Person <small>Wikipedia, DBLP bibliography & OpenAlex scholars</small>
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

        <button className="primary" disabled={busy} style={{ marginTop: "16px" }}>
          {busy ? "Investigating across sources…" : "Launch Investigation"}{" "}
          <ArrowUpRight size={16} />
        </button>
      </form>

      <p className="disclaimer" style={{ marginTop: "16px" }}>
        Strict compliance: Public sources only. Strictly no password dumps, private mailbox probing,
        credential stuffing, or CAPTCHA bypass. Matches are candidates, not proof of personal identity.
      </p>
    </section>
  );
}
