import { 
  UserCheck, 
  Mail, 
  PhoneCall, 
  GraduationCap, 
  ShieldCheck, 
  Zap, 
  ArrowRight, 
  Activity, 
  Database, 
  CheckCircle2, 
  Lock, 
  Search,
  Sparkles
} from "lucide-react";
import { IntelGraphHero } from "../components/IntelGraphHero";
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
      {/* Redesigned 2-Column Hero Section */}
      <section className="hero-grid-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="pulse-dot"></span>
            <span className="badge-text">LIVE OSINT RECONNAISSANCE ENGINE · v0.1 PRODUCTION</span>
          </div>

          <h1 className="hero-title">
            Global Multi-Source OSINT & Digital Footprint Intelligence
          </h1>

          <p className="hero-subtitle">
            Interrogate {activeCount}+ public intelligence platforms simultaneously. Discover
            digital footprints across social networks, developer hubs, telephony registries, and
            scholarly archives—with strictly zero paid API keys or recurring subscriptions.
          </p>

          <div className="hero-actions">
            <button className="btn-primary hero-btn primary-glow" onClick={onStartSearch}>
              <Search size={18} />
              <span>Launch Search Console</span>
              <ArrowRight size={16} />
            </button>
            {!currentUser ? (
              <button
                className="btn-secondary hero-btn"
                onClick={() => onOpenAuth("register")}
              >
                <Lock size={16} />
                <span>Create Free Account</span>
              </button>
            ) : (
              <div className="signed-in-pill">
                <span className="pill-dot"></span>
                <span>Active session: <strong>{currentUser.name}</strong></span>
              </div>
            )}
          </div>

          {/* Quick verification micro badges */}
          <div className="hero-trust-row">
            <div className="trust-item">
              <CheckCircle2 size={14} className="text-emerald" />
              <span>100% Free Public Sources</span>
            </div>
            <div className="trust-item">
              <ShieldCheck size={14} className="text-cyan" />
              <span>Strict Anti-SSRF Safe</span>
            </div>
            <div className="trust-item">
              <Lock size={14} className="text-violet" />
              <span>Isolated Tenant Storage</span>
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Intelligence Graph */}
        <div className="hero-visual-wrapper">
          <IntelGraphHero />
        </div>
      </section>

      {/* Global High-Impact Stats Banner */}
      <section className="hero-stats-banner">
        <div className="stat-box">
          <div className="stat-header">
            <Activity size={18} className="text-cyan" />
            <span className="stat-number">{activeCount}</span>
          </div>
          <span className="stat-label">Active Source Adapters</span>
          <span className="stat-desc">Fully tested & operational</span>
        </div>

        <div className="stat-box">
          <div className="stat-header">
            <Database size={18} className="text-emerald" />
            <span className="stat-number">100%</span>
          </div>
          <span className="stat-label">Free-Tier Ready</span>
          <span className="stat-desc">512MB RAM bounded execution</span>
        </div>

        <div className="stat-box">
          <div className="stat-header">
            <Sparkles size={18} className="text-amber" />
            <span className="stat-number">$0</span>
          </div>
          <span className="stat-label">API Cost / Subscriptions</span>
          <span className="stat-desc">Zero mandatory paid keys</span>
        </div>

        <div className="stat-box">
          <div className="stat-header">
            <Lock size={18} className="text-violet" />
            <span className="stat-number">Isolated</span>
          </div>
          <span className="stat-label">Privacy & Tenancy</span>
          <span className="stat-desc">Owner cryptographic protection</span>
        </div>
      </section>

      {/* Feature Capabilities Grid with Modern Icons & Tags */}
      <section className="section-features">
        <div className="section-header">
          <div className="section-eyebrow">
            <ShieldCheck size={14} /> INTELLIGENCE SUITE
          </div>
          <h2>Multi-Vector Intelligence Capabilities</h2>
          <p>
            Evidence-first intelligence designed for security analysts, incident responders, and OSINT researchers.
          </p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-card-header">
              <div className="feature-icon-badge icon-cyan">
                <UserCheck size={22} />
              </div>
              <span className="feature-category-pill">118+ NETWORKS</span>
            </div>
            <h3>Multi-Source Username Discovery</h3>
            <p>
              Simultaneously interrogates 118+ online services—from GitHub, Reddit, and Steam to Mastodon,
              GitLab, and Medium—using bounded async concurrency and anti-false-positive checks.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-card-header">
              <div className="feature-icon-badge icon-emerald">
                <Mail size={22} />
              </div>
              <span className="feature-category-pill">DNS & KEYRINGS</span>
            </div>
            <h3>Email Intelligence & DNS Records</h3>
            <p>
              Inspects Gravatar avatars, OpenPGP public keyrings, Mail.ru profiles, disposable provider
              lists, and DNS MX/SPF/DMARC records without sending spam.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-card-header">
              <div className="feature-icon-badge icon-amber">
                <PhoneCall size={22} />
              </div>
              <span className="feature-category-pill">E.164 TELEPHONY</span>
            </div>
            <h3>Phone & Carrier Metadata</h3>
            <p>
              Validates numbers against international E.164 specifications, detects geographic
              regions, formats carrier data, and queries public national numbering registries.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-card-header">
              <div className="feature-icon-badge icon-violet">
                <GraduationCap size={22} />
              </div>
              <span className="feature-category-pill">ACADEMIC & CITATIONS</span>
            </div>
            <h3>Scholarly & People Lookup</h3>
            <p>
              Cross-references academic citations, ORCID identifiers, arXiv preprints, CrossRef metadata,
              and Semantic Scholar publications.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-card-header">
              <div className="feature-icon-badge icon-teal">
                <ShieldCheck size={22} />
              </div>
              <span className="feature-category-pill">ZERO LEAKAGE</span>
            </div>
            <h3>Strict Privacy & Isolation</h3>
            <p>
              Every investigation is strictly isolated to its owner. Zero cross-user data leakage,
              anti-enumeration 404 responses, and immediate account deletion upon request.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-card-header">
              <div className="feature-icon-badge icon-rose">
                <Zap size={22} />
              </div>
              <span className="feature-category-pill">STREAMING TELEMETRY</span>
            </div>
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
            <div className="free-tier-badge">
              <CheckCircle2 size={14} /> PRODUCTION VERIFIED SPECIFICATION
            </div>
            <h2>Engineered Exclusively for Free-Tier Cloud Deployment</h2>
            <p>
              OpenTrace is architected from the ground up to operate reliably on free cloud tiers
              (Render, Railway, Fly.io, Vercel) within strict memory and timeout constraints.
            </p>
            <div className="free-tier-grid">
              <div className="free-tier-item">
                <CheckCircle2 size={16} className="text-emerald" />
                <div>
                  <strong>Zero Paid Dependencies</strong>
                  <p>Operates 100% on public endpoints and authorized free registries.</p>
                </div>
              </div>
              <div className="free-tier-item">
                <CheckCircle2 size={16} className="text-emerald" />
                <div>
                  <strong>Bounded Concurrency</strong>
                  <p>Guards against memory spikes, remaining strictly below 512MB RAM.</p>
                </div>
              </div>
              <div className="free-tier-item">
                <CheckCircle2 size={16} className="text-emerald" />
                <div>
                  <strong>Embedded Persistence</strong>
                  <p>Zero external DB server requirements: SQLite by default with Postgres support.</p>
                </div>
              </div>
              <div className="free-tier-item">
                <CheckCircle2 size={16} className="text-emerald" />
                <div>
                  <strong>Anti-SSRF Protection</strong>
                  <p>Blocks any internal private network requests or cloud metadata probing.</p>
                </div>
              </div>
            </div>
          </div>
          <div className="free-tier-action">
            <button className="btn-primary primary-glow" onClick={onStartSearch}>
              <span>Start Investigating Now</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
