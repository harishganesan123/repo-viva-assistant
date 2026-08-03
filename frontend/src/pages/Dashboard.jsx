import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import Layout from "../Layout";

const STATUS_STYLES = {
  analyzed: "bg-emerald-50 text-emerald-700",
  scanning: "bg-amber-50 text-amber-700",
  pending: "bg-slate-100 text-slate-600",
  failed: "bg-red-50 text-red-700",
};

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/dashboard/stats")
      .then((res) => setStats(res.data))
      .catch(() => setError("Couldn't load your dashboard. Try refreshing."));
  }, []);

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">A quick view of your repository analyses.</p>
        </div>
        <Link
          to="/analyze"
          className="rounded-lg bg-blue-600 text-white text-sm font-medium px-4 py-2 hover:bg-blue-700"
        >
          Analyze repository
        </Link>
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {stats && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-8">
            <StatCard label="Repositories analyzed" value={stats.repositories_analyzed} />
            <StatCard label="Reports generated" value={stats.reports_generated} />
            <StatCard label="Questions generated" value={stats.questions_generated} />
          </div>

          <h2 className="text-sm font-medium text-slate-700 mb-3">Recent analyses</h2>
          <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-100">
            {stats.recent.length === 0 && (
              <p className="p-6 text-sm text-slate-500">
                No repositories yet. Analyze one to see it here.
              </p>
            )}
            {stats.recent.map((repo) => (
              <Link
                key={repo.id} to={`/repos/${repo.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-slate-50"
              >
                <div>
                  <p className="text-sm font-medium text-slate-900">{repo.repo_name || repo.repo_url}</p>
                  <p className="text-xs text-slate-500">{repo.repo_url}</p>
                </div>
                <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${STATUS_STYLES[repo.status]}`}>
                  {repo.status}
                </span>
              </Link>
            ))}
          </div>
        </>
      )}
    </Layout>
  );
}
