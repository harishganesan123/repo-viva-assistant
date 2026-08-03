import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../api";
import Layout from "../Layout";

const TABS = ["Summary", "Folders", "Viva questions", "Interview questions", "Learning notes", "Insights", "Explain a file"];

function Badge({ children, tone = "slate" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-600",
    easy: "bg-emerald-50 text-emerald-700",
    medium: "bg-amber-50 text-amber-700",
    hard: "bg-red-50 text-red-700",
  };
  return <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${tones[tone] || tones.slate}`}>{children}</span>;
}

function Card({ children }) {
  return <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-3">{children}</div>;
}

export default function RepoReport() {
  const { id } = useParams();
  const [repo, setRepo] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [tab, setTab] = useState("Summary");
  const [error, setError] = useState("");

  // "Explain a file" panel state
  const [filePath, setFilePath] = useState("");
  const [functionName, setFunctionName] = useState("");
  const [fileExplanation, setFileExplanation] = useState(null);
  const [functionExplanation, setFunctionExplanation] = useState(null);
  const [explainBusy, setExplainBusy] = useState(false);
  const [explainError, setExplainError] = useState("");

  useEffect(() => {
    api.get(`/api/repos/${id}`).then((res) => setRepo(res.data)).catch(() => {});
    api
      .get(`/api/repos/${id}/analysis`)
      .then((res) => setAnalysis(res.data))
      .catch((err) => setError(err.response?.data?.detail || "This repository hasn't finished analyzing yet."));
  }, [id]);

  async function downloadReport() {
    const res = await api.get(`/api/repos/${id}/report`, { responseType: "text" });
    const blob = new Blob([res.data], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  }

  async function handleExplainFile(e) {
    e.preventDefault();
    setExplainError("");
    setExplainBusy(true);
    setFileExplanation(null);
    try {
      const res = await api.post(`/api/repos/${id}/files/explain`, { path: filePath });
      setFileExplanation(res.data);
    } catch (err) {
      setExplainError(err.response?.data?.detail || "Couldn't explain that file.");
    } finally {
      setExplainBusy(false);
    }
  }

  async function handleExplainFunction(e) {
    e.preventDefault();
    setExplainError("");
    setExplainBusy(true);
    setFunctionExplanation(null);
    try {
      const res = await api.post(`/api/repos/${id}/functions/explain`, {
        path: filePath, function_name: functionName,
      });
      setFunctionExplanation(res.data);
    } catch (err) {
      setExplainError(err.response?.data?.detail || "Couldn't explain that function.");
    } finally {
      setExplainBusy(false);
    }
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-semibold text-slate-900">{repo?.repo_name || "Repository"}</h1>
        <button
          onClick={downloadReport}
          className="rounded-lg border border-slate-300 text-sm font-medium px-4 py-2 hover:bg-slate-50"
        >
          Open full report
        </button>
      </div>
      <p className="text-sm text-slate-500 mb-6">{repo?.repo_url}</p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {analysis && (
        <>
          <div className="flex gap-1 border-b border-slate-200 mb-5 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t} onClick={() => setTab(t)}
                className={`px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 -mb-px ${
                  tab === t ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {tab === "Summary" && analysis.project_summary && (
            <div>
              <Card>
                <p className="text-xs text-slate-500 mb-1">Objective</p>
                <p className="text-sm text-slate-800">{analysis.project_summary.objective}</p>
              </Card>
              <Card>
                <p className="text-xs text-slate-500 mb-1">Overview</p>
                <p className="text-sm text-slate-800">{analysis.project_summary.overview}</p>
              </Card>
              <Card>
                <p className="text-xs text-slate-500 mb-1">Architecture</p>
                <p className="text-sm text-slate-800">{analysis.project_summary.architecture}</p>
              </Card>
              <Card>
                <p className="text-xs text-slate-500 mb-1">Tech stack</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {(analysis.project_summary.tech_stack || []).map((t) => <Badge key={t}>{t}</Badge>)}
                </div>
              </Card>
            </div>
          )}

          {tab === "Folders" && (
            <div>
              {(analysis.folder_explanations || []).length === 0 && (
                <p className="text-sm text-slate-500">No top-level folders were detected in this repo.</p>
              )}
              {(analysis.folder_explanations || []).map((f) => (
                <Card key={f.folder}>
                  <p className="text-sm font-medium text-slate-900 mb-1">{f.folder}/</p>
                  <p className="text-sm text-slate-700 mb-2">{f.purpose}</p>
                  <ul className="list-disc list-inside text-sm text-slate-600 space-y-0.5">
                    {(f.responsibilities || []).map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </Card>
              ))}
            </div>
          )}

          {tab === "Viva questions" && (
            <div>
              {(analysis.viva_questions || []).map((q, i) => (
                <Card key={i}>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge tone={q.difficulty}>{q.difficulty}</Badge>
                    <Badge>{q.category}</Badge>
                  </div>
                  <p className="text-sm font-medium text-slate-900 mb-1">{q.question}</p>
                  <p className="text-sm text-slate-700">{q.answer}</p>
                </Card>
              ))}
            </div>
          )}

          {tab === "Interview questions" && (
            <div>
              {(analysis.interview_questions || []).map((q, i) => (
                <Card key={i}>
                  <Badge>{q.topic}</Badge>
                  <p className="text-sm font-medium text-slate-900 mt-2 mb-1">{q.question}</p>
                  <p className="text-sm text-slate-700">{q.expected_answer}</p>
                </Card>
              ))}
            </div>
          )}

          {tab === "Learning notes" && (
            <div>
              {(analysis.learning_notes || []).length === 0 && (
                <p className="text-sm text-slate-500">No specific technologies were detected to build notes for.</p>
              )}
              {(analysis.learning_notes || []).map((t) => (
                <Card key={t.technology}>
                  <p className="text-sm font-medium text-slate-900 mb-1">{t.technology}</p>
                  <p className="text-sm text-slate-700">{t.explanation}</p>
                </Card>
              ))}
            </div>
          )}

          {tab === "Insights" && analysis.insights && (
            <div>
              <Card><p className="text-xs text-slate-500 mb-1">Code quality</p><p className="text-sm text-slate-800">{analysis.insights.code_quality}</p></Card>
              <Card><p className="text-xs text-slate-500 mb-1">Documentation quality</p><p className="text-sm text-slate-800">{analysis.insights.documentation_quality}</p></Card>
              <Card><p className="text-xs text-slate-500 mb-1">Security observations</p><p className="text-sm text-slate-800">{analysis.insights.security_observations}</p></Card>
              <Card>
                <p className="text-xs text-slate-500 mb-1">Improvement suggestions</p>
                <ul className="list-disc list-inside text-sm text-slate-700 space-y-0.5">
                  {(analysis.insights.improvement_suggestions || []).map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </Card>
            </div>
          )}

          {tab === "Explain a file" && (
            <div>
              <Card>
                <p className="text-xs text-slate-500 mb-2">Path relative to the repo root, e.g. backend/app/auth.py</p>
                <div className="flex gap-2 mb-3">
                  <input
                    value={filePath} onChange={(e) => setFilePath(e.target.value)}
                    placeholder="path/to/file.py"
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button onClick={handleExplainFile} disabled={explainBusy || !filePath}
                    className="rounded-lg bg-blue-600 text-white text-sm font-medium px-4 py-2 hover:bg-blue-700 disabled:opacity-60">
                    Explain file
                  </button>
                </div>
                <div className="flex gap-2">
                  <input
                    value={functionName} onChange={(e) => setFunctionName(e.target.value)}
                    placeholder="function name (optional)"
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button onClick={handleExplainFunction} disabled={explainBusy || !filePath || !functionName}
                    className="rounded-lg border border-slate-300 text-sm font-medium px-4 py-2 hover:bg-slate-50 disabled:opacity-60">
                    Explain function
                  </button>
                </div>
                {explainError && <p className="text-sm text-red-600 mt-3">{explainError}</p>}
              </Card>

              {fileExplanation && (
                <Card>
                  <p className="text-sm font-medium text-slate-900 mb-1">Purpose</p>
                  <p className="text-sm text-slate-700 mb-3">{fileExplanation.purpose}</p>
                  <p className="text-sm font-medium text-slate-900 mb-1">Role in the project</p>
                  <p className="text-sm text-slate-700">{fileExplanation.role}</p>
                </Card>
              )}

              {functionExplanation && (
                <Card>
                  <p className="text-sm font-medium text-slate-900 mb-1">Purpose</p>
                  <p className="text-sm text-slate-700 mb-3">{functionExplanation.purpose}</p>
                  <p className="text-sm font-medium text-slate-900 mb-1">Why it exists</p>
                  <p className="text-sm text-slate-700">{functionExplanation.why_it_exists}</p>
                </Card>
              )}
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
