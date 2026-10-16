import type { PlatformStats, User } from "../types";

interface LandingPageProps {
  onStartSearch: () => void;
  onOpenAuth: (mode: "login" | "register") => void;
  currentUser: User | null;
  stats?: PlatformStats | null;
}

export function LandingPage({
  onStartSearch,
  onOpenAuth,
  currentUser,
  stats,
}: LandingPageProps) {
  const activeCount = stats?.total_active_modules ?? 149;

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <span className="pulse-dot"></span> OpenTrace OSINT v0.1 · 100% Free & Open Source
        </div>
        <h1 className="hero-title">
          Unified Digital Footprint Intelligence & OSINT Search Engine
        </h1>
        <p className="hero-subtitle">
          Query {activeCount}+ active, genuinely usable public platforms in parallel.
          Verify digital footprints across social networks, developer hubs, email records,
          and public registries—with strictly zero paid API keys or subscriptions required.
        </p>

        <div className="hero-actions">
          <button className="btn-primary hero-btn" onClick={onStartSearch}>
            Launch Search Console
          </button>
          {!currentUser ? (
            <button
              className="btn-secondary hero-btn"
              onClick={() => onOpenAuth("register")}
            >
              Create Free Account
            </button>
          ) : (
            <span className="signed-in-notice">
              Logged in as <strong>{currentUser.name}</strong> ({currentUser.email})
            </span>
          )}
        </div>

        <div className="hero-stats-banner">
          <div className="stat-box">
            <span className="stat-number">{activeCount}</span>
            <span className="stat-label">Active Source Adapters</span>
          </div>
          <div className="stat-box">
            <span className="stat-number">100%</span>
            <span className="stat-label">Free-Tier Ready</span>
          </div>
          <div className="stat-box">
            <span className="stat-number">$0</span>
            <span className="stat-label">API Cost / Subscriptions</span>
          </div>
          <div className="stat-box">
            <span className="stat-number">Strict</span>
            <span className="stat-label">Privacy & Isolation</span>
          </div>
        </div>
      </section>

      {/* Feature Capabilities Grid */}
      <section className="section-features">
        <div className="section-header">
          <h2>Engine Capabilities</h2>
          <p>
            Evidence-first intelligence designed for researchers, security analysts, and investigators.
          </p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Multi-Source Username Discovery</h3>
            <p>
              Simultaneously interrogates 118+ online services—from GitHub, Reddit, and Steam to Mastodon,
              GitLab, and Medium—using bounded async concurrency and anti-false-positive checks.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">✉️</div>
            <h3>Email Intelligence & DNS Records</h3>
            <p>
              Inspects Gravatar avatars, OpenPGP public keyrings, Mail.ru profiles, disposable provider
              lists, and DNS MX/SPF/DMARC records without sending spam.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📞</div>
            <h3>Phone & Carrier Metadata</h3>
            <p>
              Validates numbers against international E.164 specifications, detects geographic
              regions, formats carrier data, and queries public national numbering registries.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎓</div>
            <h3>Scholarly & People Lookup</h3>
            <p>
              Cross-references academic citations, ORCID identifiers, arXiv preprints, CrossRef metadata,
              and Semantic Scholar publications.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3>Strict Privacy & Isolation</h3>
            <p>
              Every investigation is strictly isolated to its owner. Zero cross-user data leakage,
              anti-enumeration 404 responses, and immediate account deletion upon request.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Live SSE Streaming & Retries</h3>
            <p>
              Streams finding events directly to your browser via Server-Sent Events. Failed or rate-limited
              sources can be retried with one click.
            </p>
          </div>
        </div>
      </section>

      {/* Architecture & Free-Tier Promise */}
      <section className="section-free-tier">
        <div className="free-tier-card">
          <div className="free-tier-content">
            <h2>Built Specifically for Free-Tier Deployment</h2>
            <p>
              OpenTrace is engineered from the ground up to operate reliably on free cloud hosting
              (Render, Railway, Fly.io, Vercel) within strict memory and timeout constraints.
            </p>
            <ul className="free-tier-list">
              <li>✓ No paid third-party dependencies or surprise usage fees</li>
              <li>✓ Bounded concurrency preventing memory exhaustion on 512MB RAM containers</li>
              <li>✓ SQLite default database with zero external server management overhead</li>
              <li>✓ Anti-SSRF guards preventing outbound abuse to internal private networks</li>
            </ul>
          </div>
          <div className="free-tier-action">
            <button className="btn-primary" onClick={onStartSearch}>
              Start Investigating Now
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
