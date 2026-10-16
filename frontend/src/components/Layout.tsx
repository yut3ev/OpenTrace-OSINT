import React from "react";
import { Fingerprint, RefreshCw } from "lucide-react";

interface LayoutProps {
  onRefresh: () => void;
  children: React.ReactNode;
}

export function Layout({ onRefresh, children }: LayoutProps) {
  return (
    <main className="shell">
      <header className="header">
        <div className="brand">
          <div className="brandIcon">
            <Fingerprint />
          </div>
          <div>
            <h1>
              OpenTrace<span>.</span>
            </h1>
            <p>Public digital-footprint intelligence</p>
          </div>
        </div>
        <button className="ghost" onClick={onRefresh} aria-label="Refresh data">
          <RefreshCw size={16} /> Refresh
        </button>
      </header>

      {children}

      <footer>
        <span>OpenTrace OSINT · v0.1.0</span>
        <span>Public sources only · Findings are not identity proof</span>
      </footer>
    </main>
  );
}
