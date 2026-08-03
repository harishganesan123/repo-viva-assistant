import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Layout from "../Layout";

export default function Analyze() {
  const [repoUrl, setRepoUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await api.post("/api/repos/analyze", { repo_url: repoUrl });
      navigate(`/repos/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Check the URL and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Analyze a repository</h1>
      <p className="text-sm text-slate-500 mb-6">
        Paste a public GitHub repository URL. This clones it, reads the structure and key files,
        and generates a full viva and interview prep report.
      </p>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 max-w-xl">
        <label className="block text-sm text-slate-600 mb-1">GitHub repository URL</label>
        <input
          type="url" required value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="https://github.com/username/project-repo"
        />
        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
        <button
          type="submit" disabled={busy}
          className="mt-4 rounded-lg bg-blue-600 text-white text-sm font-medium px-4 py-2.5 hover:bg-blue-700 disabled:opacity-60"
        >
          {busy ? "Cloning and analyzing… this can take a minute" : "Run analysis"}
        </button>
      </form>
    </Layout>
  );
}
