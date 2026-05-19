import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  createPathway,
  getPathway,
  updatePathway,
  uploadResume,
  getModelCatalogue,
} from "../lib/api";

const initialForm = {
  name: "",
  role_category: "",
  industry: "",
  skills: [],
  location: "",
  remote_type: "any",
  min_stipend: "",
  job_provider: "mock",
  sheets_sync: false,
  calendar_followup: false,
  llm_mode: "auto",
  llm_tier: "auto",
  llm_manual_model: "",
  llm_agent_extract: "",
  llm_agent_classify: "",
  llm_agent_research: "",
  llm_agent_draft: "",
};

export default function PathwayConfig() {
  const { id } = useParams();
  const nav = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [resumeFile, setResumeFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [catalogue, setCatalogue] = useState([]);

  useEffect(() => {
    getModelCatalogue().then(setCatalogue).catch(() => {});
    if (id) {
      getPathway(id).then((data) => {
        setForm({
          ...initialForm,
          ...data,
          min_stipend: data.min_stipend || "",
          skills: data.skills || [],
        });
      });
    }
  }, [id]);

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...form,
        min_stipend: form.min_stipend ? Number(form.min_stipend) : null,
        skills: Array.isArray(form.skills)
          ? form.skills
          : String(form.skills || "")
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
      };

      let saved;
      if (id) saved = await updatePathway(id, payload);
      else saved = await createPathway(payload);

      if (resumeFile) {
        await uploadResume(saved.id, resumeFile);
      }

      nav("/dashboard");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="label-caps mb-2">Pathway Setup</div>
        <h1 className="font-display text-5xl font-black leading-none m-0">
          {id ? "Edit Pathway" : "New Pathway"}
        </h1>
        <p className="mt-3 text-zinc-600 max-w-3xl">
          Configure role filters, resume, job provider, and LLM routing for this pathway.
        </p>
      </div>

      <form onSubmit={onSubmit} className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="bg-white brutal-border p-6">
          <div className="label-caps mb-4">Role Settings</div>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Pathway name</label>
            <input
              className="w-full brutal-border p-3"
              value={form.name}
              onChange={(e) => setField("name", e.target.value)}
              placeholder="BA / Strategy Ops"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Role category</label>
            <input
              className="w-full brutal-border p-3"
              value={form.role_category}
              onChange={(e) => setField("role_category", e.target.value)}
              placeholder="Business Analyst, Strategy Ops, Product, Growth..."
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Industry</label>
            <input
              className="w-full brutal-border p-3"
              value={form.industry || ""}
              onChange={(e) => setField("industry", e.target.value)}
              placeholder="Fintech / SaaS / AI / Devtools"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Skills (comma separated)</label>
            <input
              className="w-full brutal-border p-3"
              value={Array.isArray(form.skills) ? form.skills.join(", ") : form.skills}
              onChange={(e) => setField("skills", e.target.value)}
              placeholder="Python, SQL, Excel, Communication"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Location</label>
              <input
                className="w-full brutal-border p-3"
                value={form.location || ""}
                onChange={(e) => setField("location", e.target.value)}
                placeholder="Mumbai / Bangalore / Remote"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Remote type</label>
              <select
                className="w-full brutal-border p-3"
                value={form.remote_type}
                onChange={(e) => setField("remote_type", e.target.value)}
              >
                <option value="any">Any</option>
                <option value="remote">Remote</option>
                <option value="onsite">Onsite</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Min stipend</label>
              <input
                className="w-full brutal-border p-3"
                type="number"
                value={form.min_stipend}
                onChange={(e) => setField("min_stipend", e.target.value)}
                placeholder="15000"
              />
            </div>
          </div>
        </section>

        <section className="bg-white brutal-border p-6">
          <div className="label-caps mb-4">Resume & Job Provider</div>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Upload resume</label>
            <input
              className="w-full brutal-border p-3 bg-white"
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Job data provider</label>
            <select
              className="w-full brutal-border p-3"
              value={form.job_provider || "mock"}
              onChange={(e) => setField("job_provider", e.target.value)}
            >
              <option value="mock">Mock</option>
              <option value="apify">Apify</option>
            </select>
          </div>

          <div className="flex flex-col gap-3">
            <label className="inline-flex items-center gap-3">
              <input
                type="checkbox"
                checked={!!form.sheets_sync}
                onChange={(e) => setField("sheets_sync", e.target.checked)}
              />
              <span>Google Sheets sync</span>
            </label>

            <label className="inline-flex items-center gap-3">
              <input
                type="checkbox"
                checked={!!form.calendar_followup}
                onChange={(e) => setField("calendar_followup", e.target.checked)}
              />
              <span>Calendar follow-up</span>
            </label>
          </div>
        </section>

        <section className="bg-white brutal-border p-6 xl:col-span-2">
          <div className="label-caps mb-4">LLM Routing</div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
            <div>
              <label className="block text-sm font-semibold mb-2">LLM mode</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_mode}
                onChange={(e) => setField("llm_mode", e.target.value)}
              >
                <option value="auto">Auto</option>
                <option value="manual">Manual</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Tier</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_tier}
                onChange={(e) => setField("llm_tier", e.target.value)}
              >
                <option value="auto">Auto (recommended)</option>
                <option value="cheap">Cheap / eco</option>
                <option value="balanced">Balanced</option>
                <option value="premium">Premium quality</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Manual model</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_manual_model}
                onChange={(e) => setField("llm_manual_model", e.target.value)}
              >
                <option value="">Use router default</option>
                {catalogue.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Extract agent</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_agent_extract}
                onChange={(e) => setField("llm_agent_extract", e.target.value)}
              >
                <option value="">Use global</option>
                {catalogue.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Classify agent</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_agent_classify}
                onChange={(e) => setField("llm_agent_classify", e.target.value)}
              >
                <option value="">Use global</option>
                {catalogue.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Research agent</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_agent_research}
                onChange={(e) => setField("llm_agent_research", e.target.value)}
              >
                <option value="">Use global</option>
                {catalogue.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Drafting agent</label>
              <select
                className="w-full brutal-border p-3"
                value={form.llm_agent_draft}
                onChange={(e) => setField("llm_agent_draft", e.target.value)}
              >
                <option value="">Use global</option>
                {catalogue.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <div className="xl:col-span-2 flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-3 bg-black text-white font-semibold"
          >
            {saving ? "Saving..." : "Save Pathway"}
          </button>
        </div>
      </form>
    </div>
  );
}