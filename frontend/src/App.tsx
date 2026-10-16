import { useEffect, useState } from "react";
import { api, authStorage } from "./api/client";
import { AuthModal } from "./components/AuthModal";
import { Layout, NavTab } from "./components/Layout";
import { SourcesCatalog } from "./components/SourcesCatalog";
import { Dashboard } from "./pages/Dashboard";
import { FeaturesPage } from "./pages/FeaturesPage";
import { InvestigationDetail } from "./pages/InvestigationDetail";
import { LandingPage } from "./pages/LandingPage";
import { PrivacyTermsPage } from "./pages/PrivacyTermsPage";
import type { Investigation, InvestigationRequest, ModuleInfo, PlatformStats, User } from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>("home");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "register">("login");

  const [current, setCurrent] = useState<Investigation | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<Investigation | null>(null);
  const [history, setHistory] = useState<Investigation[]>([]);
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [stats, setStats] = useState<PlatformStats | null>(null);

  async function checkAuth() {
    const token = authStorage.getToken();
    if (!token) {
      setCurrentUser(null);
      return;
    }
    try {
      const user = await api.auth.me();
      setCurrentUser(user);
    } catch {
      authStorage.setToken(null);
      setCurrentUser(null);
    }
  }

  async function refresh() {
    try {
      const [items, mods, st] = await Promise.all([
        api.list().catch(() => []),
        api.modules().catch(() => []),
        api.stats().catch(() => null),
      ]);
      setHistory(items);
      setModules(mods);
      if (st) setStats(st);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to connect to API");
    }
  }

  useEffect(() => {
    void checkAuth();
    void refresh();
  }, []);

  async function handleLogout() {
    try {
      await api.auth.logout();
    } catch {
      // Continue client cleanup even if network request fails
    }
    authStorage.setToken(null);
    setCurrentUser(null);
    await refresh();
  }

  function handleOpenAuth(mode: "login" | "register") {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  }

  async function handleAuthSuccess(user: User) {
    setCurrentUser(user);
    await refresh();
    setActiveTab("console");
  }

  async function handleSubmit(payload: InvestigationRequest) {
    setBusy(true);
    setError("");
    try {
      const result = await api.create(payload);
      setCurrent(result);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Investigation failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleOpenHistory(id: string) {
    setError("");
    try {
      const inv = await api.get(id);
      setSelectedDetail(inv);
      setActiveTab("console");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load investigation");
    }
  }

  async function handleDeleteHistory(id: string) {
    try {
      await api.delete(id);
      if (selectedDetail?.id === id) {
        setSelectedDetail(null);
      }
      if (current?.id === id) {
        setCurrent(null);
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to delete investigation");
    }
  }

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={(tab) => {
        setActiveTab(tab);
        if (tab !== "console") setSelectedDetail(null);
      }}
      currentUser={currentUser}
      onOpenAuth={handleOpenAuth}
      onLogout={handleLogout}
      onRefresh={() => void refresh()}
    >
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {/* Landing Page */}
      {activeTab === "home" && (
        <LandingPage
          onStartSearch={() => setActiveTab("console")}
          onOpenAuth={handleOpenAuth}
          currentUser={currentUser}
          stats={stats}
        />
      )}

      {/* Investigation Console */}
      {activeTab === "console" &&
        (selectedDetail ? (
          <InvestigationDetail
            investigation={selectedDetail}
            onBack={() => setSelectedDetail(null)}
            onUpdate={(updated) => {
              setSelectedDetail(updated);
              void refresh();
            }}
          />
        ) : (
          <Dashboard
            current={current}
            history={history}
            modules={modules}
            busy={busy}
            onSubmit={handleSubmit}
            onSelectHistory={handleOpenHistory}
            onDeleteHistory={handleDeleteHistory}
          />
        ))}

      {/* Standalone Sources Catalog Tab */}
      {activeTab === "sources" && (
        <div className="panel" style={{ marginTop: "1rem" }}>
          <div className="sectionTitle">
            <span className="number">SRC</span>
            <div>
              <h2>Source Catalog & Adapter Registry</h2>
              <p>Explore all 149 registered sources, categories, and real-time health checks.</p>
            </div>
          </div>
          <SourcesCatalog />
        </div>
      )}

      {/* Features & Architecture Page */}
      {activeTab === "features" && (
        <FeaturesPage onBackToConsole={() => setActiveTab("console")} />
      )}

      {/* Ethics & Privacy Policy Page */}
      {activeTab === "privacy" && (
        <PrivacyTermsPage onBackToConsole={() => setActiveTab("console")} />
      )}

      {/* Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        initialMode={authModalMode}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </Layout>
  );
}
