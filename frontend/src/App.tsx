import { useEffect, useState } from "react";
import { api } from "./api/client";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { InvestigationDetail } from "./pages/InvestigationDetail";
import type { Investigation, InvestigationRequest, ModuleInfo } from "./types";

export default function App() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [current, setCurrent] = useState<Investigation | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<Investigation | null>(null);
  const [history, setHistory] = useState<Investigation[]>([]);
  const [modules, setModules] = useState<ModuleInfo[]>([]);

  async function refresh() {
    try {
      const [items, mods] = await Promise.all([api.list(), api.modules()]);
      setHistory(items);
      setModules(mods);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to connect to API");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

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
    <Layout onRefresh={() => void refresh()}>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {selectedDetail ? (
        <InvestigationDetail
          investigation={selectedDetail}
          onBack={() => setSelectedDetail(null)}
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
      )}
    </Layout>
  );
}
