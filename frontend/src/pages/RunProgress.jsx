import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getStatus, runPathway } from "../lib/api";

export default function RunProgress() {
  const { id } = useParams();
  const [status, setStatus] = useState(null);
  const [starting, setStarting] = useState(false);

  async function refresh() {
    try {
      const s = await getStatus(id);
      setStatus(s);
    } catch (error) {
      console.error("Failed to fetch status", error);
    }
  }

  async function startRun() {
    setStarting(true);
    try {
      await runPathway(id);
      await refresh();
    } catch (error) {
      console.error("Failed to start run", error);
    } finally {
      setStarting(false);
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, [id]);

  return (
    <div className="p-8">
      <div className="label-caps mb-2">Agent Progress</div>
      <h1 className="font-display text-5xl font-black leading-none m-0">
        Run Pathway
      </h1>

      <div className="mt-8 bg-white brutal-border p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="label-caps mb-1">Current Status</div>
            <div className="text-lg font-semibold">
              {status?.status || "idle"}
            </div>
            <div className="text-sm text-zinc-600 mt-1">
              {status?.stage || "not started"}
            </div>
          </div>

          <button
            onClick={startRun}
            disabled={starting}
            className="px-5 py-3 bg-black text-white font-semibold"
          >
            {starting ? "Starting..." : "Run Agents"}
          </button>
        </div>

        <div className="label-caps mb-3">Stage Logs</div>
        <div className="bg-[#f7f7f7] brutal-border p-4 min-h-[260px] font-mono text-sm whitespace-pre-wrap">
          {(status?.stage_logs || []).length
            ? status.stage_logs.join("\n")
            : "No logs yet."}
        </div>
      </div>
    </div>
  );
}