import React, { useState } from "react";
import { 
  Globe, 
  Mail, 
  Phone, 
  GraduationCap, 
  Activity, 
  CheckCircle2, 
  Lock,
  Search,
  Terminal,
  Radio
} from "lucide-react";

interface NodeData {
  id: string;
  label: string;
  category: string;
  status: "verified" | "active" | "secured";
  detail: string;
  x: number;
  y: number;
  icon: React.ReactNode;
}

export function IntelGraphHero() {
  const [activeNode, setActiveNode] = useState<string>("social");

  const nodes: NodeData[] = [
    {
      id: "social",
      label: "Social & Dev Footprint",
      category: "118+ Networks",
      status: "verified",
      detail: "GitHub, Reddit, GitLab, Mastodon, Medium",
      x: 18,
      y: 22,
      icon: <Globe size={16} className="text-cyan-400" />,
    },
    {
      id: "email",
      label: "Email & DNS Telemetry",
      category: "Mail & Records",
      status: "verified",
      detail: "Gravatar, OpenPGP, MX, SPF, DMARC Validation",
      x: 82,
      y: 20,
      icon: <Mail size={16} className="text-emerald-400" />,
    },
    {
      id: "phone",
      label: "Telephony & Carrier",
      category: "E.164 Specs",
      status: "active",
      detail: "Carrier routing, geo-origin, public allocations",
      x: 85,
      y: 78,
      icon: <Phone size={16} className="text-amber-400" />,
    },
    {
      id: "scholarly",
      label: "Scholarly & Academia",
      category: "Publications",
      status: "verified",
      detail: "ORCID IDs, arXiv preprints, Semantic Scholar",
      x: 15,
      y: 76,
      icon: <GraduationCap size={16} className="text-indigo-400" />,
    },
    {
      id: "breach",
      label: "Passive Keyrings & Certs",
      category: "Public Crypto",
      status: "secured",
      detail: "OpenPGP key servers, TLS crt.sh metadata",
      x: 50,
      y: 92,
      icon: <Lock size={16} className="text-teal-400" />,
    },
  ];

  const currentNode = nodes.find((n) => n.id === activeNode) || nodes[0];

  return (
    <div className="intel-hero-card">
      {/* Top Cyber HUD Bar */}
      <div className="intel-hud-bar">
        <div className="hud-telemetry">
          <span className="hud-indicator active"></span>
          <span className="hud-label">OSINT RECONNAISSANCE GRID</span>
        </div>
        <div className="hud-stats">
          <span className="hud-pill"><Radio size={12} /> LIVE</span>
          <span className="hud-pill mono">149 SOURCES</span>
          <span className="hud-pill mono text-emerald">0 PAID KEYS</span>
        </div>
      </div>

      {/* Center Interactive Graph Canvas */}
      <div className="intel-canvas-wrapper">
        <svg className="intel-svg-canvas" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="cyberLineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="activeLineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.4" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Grid lines in SVG */}
          <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(56, 189, 248, 0.07)" strokeDasharray="2,3" />
          <circle cx="50" cy="50" r="26" fill="none" stroke="rgba(56, 189, 248, 0.12)" strokeDasharray="3,3" />
          <circle cx="50" cy="50" r="10" fill="none" stroke="rgba(16, 185, 129, 0.2)" />

          {/* Connection Lines from Center (50, 50) to each Node */}
          {nodes.map((node) => {
            const isActive = node.id === activeNode;
            return (
              <g key={`edge-${node.id}`}>
                <line
                  x1="50"
                  y1="50"
                  x2={node.x}
                  y2={node.y}
                  stroke={isActive ? "url(#activeLineGrad)" : "url(#cyberLineGrad)"}
                  strokeWidth={isActive ? "1.2" : "0.7"}
                  strokeDasharray={isActive ? "none" : "2,2"}
                  className={isActive ? "active-beam" : "passive-beam"}
                />
                {isActive && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="2.5"
                    fill="#38bdf8"
                    filter="url(#glow)"
                  />
                )}
              </g>
            );
          })}
        </svg>

        {/* Central Investigation Target Node */}
        <div className="intel-center-node">
          <div className="center-radar-ring"></div>
          <div className="center-radar-ring delay-1"></div>
          <div className="center-core">
            <Search size={18} className="center-icon" />
            <span className="center-tag">TARGET</span>
          </div>
        </div>

        {/* Orbiting Satellite Nodes */}
        {nodes.map((node) => {
          const isActive = node.id === activeNode;
          return (
            <button
              key={node.id}
              className={`intel-satellite-node ${isActive ? "selected" : ""}`}
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
              onClick={() => setActiveNode(node.id)}
              onMouseEnter={() => setActiveNode(node.id)}
              aria-label={`Select ${node.label}`}
            >
              <div className="satellite-icon-box">{node.icon}</div>
              <div className="satellite-info">
                <span className="satellite-title">{node.label}</span>
                <span className="satellite-badge">{node.category}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Bottom Live Inspector Detail */}
      <div className="intel-inspector-footer">
        <div className="inspector-meta">
          <div className="meta-header">
            <Terminal size={14} className="text-cyan" />
            <span className="meta-source-label">ACTIVE ADAPTER CLUSTER:</span>
            <strong className="meta-source-title">{currentNode.label}</strong>
          </div>
          <p className="meta-detail-text">{currentNode.detail}</p>
        </div>
        <div className="inspector-status">
          <span className="inspector-pill">
            <CheckCircle2 size={13} className="text-emerald" />
            <span>Anti-FP Verified</span>
          </span>
          <span className="inspector-pill">
            <Activity size={13} className="text-cyan" />
            <span>&lt; 1.2s Bounded Concurrency</span>
          </span>
        </div>
      </div>
    </div>
  );
}
