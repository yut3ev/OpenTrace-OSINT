import React from "react";
import { Fingerprint, LogIn, LogOut, RefreshCw, Shield, User as UserIcon } from "lucide-react";
import type { User } from "../types";

export type NavTab = "home" | "console" | "sources" | "features" | "privacy";

interface LayoutProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  currentUser: User | null;
  onOpenAuth: (mode: "login" | "register") => void;
  onLogout: () => void;
  onRefresh: () => void;
  children: React.ReactNode;
}

export function Layout({
  activeTab,
  onTabChange,
  currentUser,
  onOpenAuth,
  onLogout,
  onRefresh,
  children,
}: LayoutProps) {
  return (
    <main className="shell">
      <header className="header">
        <div className="brand" onClick={() => onTabChange("home")} style={{ cursor: "pointer" }}>
          <div className="brandIcon">
            <Fingerprint />
          </div>
          <div>
            <h1>
              OpenTrace<span>.</span>
            </h1>
            <p>Multi-Source Public OSINT Engine</p>
          </div>
        </div>

        <nav className="header-nav">
          <button
            className={`nav-btn ${activeTab === "home" ? "active" : ""}`}
            onClick={() => onTabChange("home")}
          >
            Home
          </button>
          <button
            className={`nav-btn ${activeTab === "console" ? "active" : ""}`}
            onClick={() => onTabChange("console")}
          >
            Console
          </button>
          <button
            className={`nav-btn ${activeTab === "sources" ? "active" : ""}`}
            onClick={() => onTabChange("sources")}
          >
            Sources (149)
          </button>
          <button
            className={`nav-btn ${activeTab === "features" ? "active" : ""}`}
            onClick={() => onTabChange("features")}
          >
            Features
          </button>
          <button
            className={`nav-btn ${activeTab === "privacy" ? "active" : ""}`}
            onClick={() => onTabChange("privacy")}
          >
            Ethics & Privacy
          </button>
        </nav>

        <div className="header-actions">
          <button className="ghost" onClick={onRefresh} aria-label="Refresh data">
            <RefreshCw size={15} /> Refresh
          </button>

          {currentUser ? (
            <div className="user-profile-menu">
              <span className="user-pill">
                <UserIcon size={14} /> {currentUser.name}
                {currentUser.role === "admin" && <span className="admin-tag">ADMIN</span>}
              </span>
              <button
                className="ghost btn-logout"
                onClick={onLogout}
                title="Log out session"
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <div className="auth-nav-buttons">
              <button
                className="ghost btn-auth-login"
                onClick={() => onOpenAuth("login")}
              >
                <LogIn size={15} /> Sign In
              </button>
              <button
                className="btn-primary btn-sm btn-auth-register"
                onClick={() => onOpenAuth("register")}
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </header>

      {children}

      <footer className="footer-bar">
        <div className="footer-left">
          <span>OpenTrace OSINT · v0.1.0 · Free & Open-Source</span>
          <span>Zero Paid APIs · Bounded Asynchronous Scheduling</span>
        </div>
        <div className="footer-right">
          <button className="footer-link" onClick={() => onTabChange("privacy")}>
            <Shield size={12} /> Safe Harbor & Ethics Policy
          </button>
          <span> · </span>
          <button className="footer-link" onClick={() => onTabChange("features")}>
            Architecture Specs
          </button>
        </div>
      </footer>
    </main>
  );
}
