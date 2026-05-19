import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getInternships,
  getUnlisted,
  exportInternshipsUrl,
  exportUnlistedUrl,
} from "../lib/api";

export default function PathwayResults() {
  const { id } = useParams();
  const [internships, setInternships] = useState([]);
  const [unlisted, setUnlisted] = useState([]);

  useEffect(() => {
    getInternships(id)
      .then(setInternships)
      .catch(() => {});

    getUnlisted(id)
      .then(setUnlisted)
      .catch(() => {});
  }, [id]);

  return (
    <div className="p-8">
      <div className="label-caps mb-2">Results</div>
      <h1 className="font-display text-5xl font-black leading-none m-0">
        Pathway Results
      </h1>

      <div className="flex gap-3 mt-5 mb-8">
        <a
          href={exportInternshipsUrl(id)}
          className="px-4 py-3 bg-black text-white text-sm font-semibold"
        >
          Export Listed CSV
        </a>

        <a
          href={exportUnlistedUrl(id)}
          className="px-4 py-3 brutal-border bg-white text-sm font-semibold"
        >
          Export Unlisted CSV
        </a>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="bg-white brutal-border">
          <div className="px-5 py-4 brutal-border border-x-0 border-t-0">
            <div className="font-display text-2xl font-bold">
              Listed Internships
            </div>
          </div>

          <div className="p-4 space-y-3">
            {internships.length > 0 ? (
              internships.map((job) => (
                <div key={job.id} className="brutal-border p-4">
                  <div className="font-semibold">{job.title}</div>
                  <div className="text-sm text-zinc-600">
                    {job.company} · {job.location}
                  </div>
                  <div className="text-xs text-zinc-500 mt-2">
                    {job.source} · {job.posted_date}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-zinc-500">No listed internships yet.</div>
            )}
          </div>
        </section>

        <section className="bg-white brutal-border">
          <div className="px-5 py-4 brutal-border border-x-0 border-t-0">
            <div className="font-display text-2xl font-bold">
              Unlisted Companies
            </div>
          </div>

          <div className="p-4 space-y-3">
            {unlisted.length > 0 ? (
              unlisted.map((c) => (
                <div key={c.id} className="brutal-border p-4">
                  <div className="font-semibold">{c.company_name}</div>
                  <div className="text-sm text-zinc-600">
                    Score: {c.relevance_score} · Email:{" "}
                    {c.contact_email || "Not found"}
                  </div>
                  <div className="text-xs text-zinc-500 mt-2">
                    {c.website_url}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-zinc-500">No unlisted companies yet.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}