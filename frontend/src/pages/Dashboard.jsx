import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, listPathways } from "../lib/api";

function StatusBadge({ status }) {
  const cls =
    status === "running"
      ? "status-badge status-running"
      : status === "completed"
      ? "status-badge status-completed"
      : status === "error"
      ? "status-badge status-error"
      : "status-badge status-idle";

  return <span className={cls}>{status || "idle"}</span>;
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [pathways, setPathways] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [s, p] = await Promise.all([getStats(), listPathways()]);
      setStats(s);
      setPathways(p);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="p-8">
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <div className="label-caps mb-2">Control Room</div>
          <h1 className="font-display text-5xl font-black leading-none m-0">
            Dashboard
          </h1>
          <p className="mt-3 text-zinc-600 max-w-2xl">
            Track pathways, agents, internships, unlisted companies, and outreach.
          </p>
        </div>

        <Link
          to="/pathways/new"
          className="inline-flex items-center gap-2 px-4 py-3 bg-black text-white text-sm font-semibold"
        >
          + New Pathway
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
        <div className="bg-white brutal-border p-5">
          <div className="label-caps mb-3">Total Pathways</div>
          <div className="font-display text-4xl font-black">
            {stats ? stats.pathways : "—"}
          </div>
        </div>

        <div className="bg-white brutal-border p-5">
          <div className="label-caps mb-3">Running</div>
          <div className="font-display text-4xl font-black">
            {stats ? stats.running : "—"}
          </div>
        </div>

        <div className="bg-white brutal-border p-5">
          <div className="label-caps mb-3">Drafts</div>
          <div className="font-display text-4xl font-black">
            {stats ? stats.drafts : "—"}
          </div>
        </div>

        <div className="bg-white brutal-border p-5">
          <div className="label-caps mb-3">Emails Sent</div>
          <div className="font-display text-4xl font-black">
            {stats ? stats.emails_sent : "—"}
          </div>
        </div>
      </div>

      <div className="bg-white brutal-border">
        <div className="px-5 py-4 brutal-border border-x-0 border-t-0 flex items-center justify-between">
          <div>
            <div className="label-caps mb-1">Pathways</div>
            <div className="text-sm text-zinc-600">
              Up to 5 role-based pathways
            </div>
          </div>
        </div>

        {loading ? (
          <div className="p-6 text-zinc-500">Loading dashboard...</div>
        ) : pathways.length === 0 ? (
          <div className="p-8">
            <div className="font-display text-3xl font-bold mb-2">No pathways yet</div>
            <p className="text-zinc-600 mb-5 max-w-xl">
              Create your first pathway to start scraping listed jobs, finding unlisted companies,
              discovering contacts, understanding your resume, and drafting emails.
            </p>
            <Link
              to="/pathways/new"
              className="inline-flex items-center gap-2 px-4 py-3 bg-black text-white text-sm font-semibold"
            >
              + Create first pathway
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 p-4">
            {pathways.map((p) => (
              <div key={p.id} className="bg-[#fcfcfc] brutal-border p-5">
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div>
                    <div className="font-display text-2xl font-bold">{p.name}</div>
                    <div className="text-sm text-zinc-600 mt-1">
                      {p.role_category}
                    </div>
                  </div>
                  <StatusBadge status={p.status} />
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm mb-5">
                  <div>
                    <div className="label-caps mb-1">Location</div>
                    <div>{p.location || "Any"}</div>
                  </div>
                  <div>
                    <div className="label-caps mb-1">Remote</div>
                    <div>{p.remote_type || "any"}</div>
                  </div>
                  <div>
                    <div className="label-caps mb-1">Job Provider</div>
                    <div>{p.job_provider || "mock"}</div>
                  </div>
                  <div>
                    <div className="label-caps mb-1">LLM Tier</div>
                    <div>{p.llm_tier || "auto"}</div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link to={`/pathways/${p.id}/edit`} className="px-3 py-2 brutal-border text-sm bg-white">
                    Configure
                  </Link>
                  <Link to={`/pathways/${p.id}/run`} className="px-3 py-2 brutal-border text-sm bg-white">
                    Run
                  </Link>
                  <Link to={`/pathways/${p.id}/results`} className="px-3 py-2 brutal-border text-sm bg-white">
                    Results
                  </Link>
                  <Link to={`/pathways/${p.id}/emails`} className="px-3 py-2 bg-black text-white text-sm">
                    Review Emails
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}