import React, { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import type { InvestigationRequest } from "../types";

interface InvestigationFormProps {
  onSubmit: (payload: InvestigationRequest) => Promise<void>;
  busy: boolean;
}

export function InvestigationForm({ onSubmit, busy }: InvestigationFormProps) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [localError, setLocalError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: InvestigationRequest = {};
    if (username.trim()) payload.username = username.trim();
    if (email.trim()) payload.email = email.trim();
    if (phone.trim()) payload.phone = phone.trim();

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
          <h2>New investigation</h2>
          <p>Use identifiers you own or are authorized to research.</p>
        </div>
      </div>

      {localError && <div className="error" role="alert">{localError}</div>}

      <form onSubmit={handleSubmit}>
        <label htmlFor="username">
          Username <small>Public profiles only</small>
        </label>
        <input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="e.g. octocat"
          maxLength={100}
        />

        <label htmlFor="email">
          Email <small>Syntax + DNS metadata</small>
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="e.g. user@example.com"
          maxLength={254}
        />

        <label htmlFor="phone">
          Phone <small>Include country code</small>
        </label>
        <input
          id="phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="e.g. +12025550123"
          maxLength={40}
        />

        <button className="primary" disabled={busy}>
          {busy ? "Running modules…" : "Run investigation"} <ArrowUpRight size={16} />
        </button>
      </form>

      <p className="disclaimer">
        No private account access, mailbox probing, subscriber identification or credential searches.
      </p>
    </section>
  );
}
