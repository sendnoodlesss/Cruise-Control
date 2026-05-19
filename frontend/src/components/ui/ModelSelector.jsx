/**
 * ModelSelector — full LLM model picker with:
 *   - Auto mode (smart tier: cheap/balanced/premium/auto)
 *   - Manual mode (pick any of 35+ models grouped by provider)
 *   - Per-agent overrides (optional advanced panel)
 *
 * Props:
 *   value    – { llm_mode, llm_tier, llm_manual_model,
 *                llm_agent_extract, llm_agent_classify,
 *                llm_agent_research, llm_agent_draft }
 *   onChange – called with updated object
 *   compact  – show single-line selector (for pathway cards)
 */
import { useState, useEffect } from "react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";

const TIERS = [
  { value: "auto",     label: "🤖 Auto (smart per-task)",      desc: "Cheap for parsing, premium for emails" },
  { value: "cheap",    label: "⚡ Cheap / Eco",                 desc: "Smallest free model for everything" },
  { value: "balanced", label: "⚖️  Balanced",                   desc: "Mid-size models, good quality" },
  { value: "premium",  label: "🏆 Premium quality",             desc: "Best model for every task" },
];

const AGENT_LABELS = {
  llm_agent_extract:  "📄 Resume Extractor",
  llm_agent_classify: "🏷️  Relevance Scorer",
  llm_agent_research: "🔍 Company Researcher",
  llm_agent_draft:    "✉️  Email Drafter",
};

const PROVIDER_BADGE = {
  groq:      { bg: "#FFF3E0", color: "#E65100", label: "Groq (Free)" },
  together:  { bg: "#E3F2FD", color: "#1565C0", label: "Together AI" },
  openai:    { bg: "#E8F5E9", color: "#1B5E20", label: "OpenAI" },
  anthropic: { bg: "#F3E5F5", color: "#4A148C", label: "Anthropic" },
  lmstudio:  { bg: "#FFFDE7", color: "#F57F17", label: "LM Studio (local)" },
  ollama:    { bg: "#E0F2F1", color: "#004D40", label: "Ollama (local)" },
};

export default function ModelSelector({ value = {}, onChange, compact = false }) {
  const [models, setModels]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const s = {
    llm_mode:           value.llm_mode           || "auto",
    llm_tier:           value.llm_tier           || "auto",
    llm_manual_model:   value.llm_manual_model   || "",
    llm_agent_extract:  value.llm_agent_extract  || "",
    llm_agent_classify: value.llm_agent_classify || "",
    llm_agent_research: value.llm_agent_research || "",
    llm_agent_draft:    value.llm_agent_draft    || "",
  };

  const upd = (key, val) => onChange({ ...s, [key]: val });

  useEffect(() => {
    fetch(`${BACKEND}/api/models/available`)
      .then(r => r.json())
      .then(data => { setModels(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  // Group by provider
  const grouped = models.reduce((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = [];
    acc[m.provider].push(m);
    return acc;
  }, {});

  /* ── Compact single-line version (for pathway cards) ── */
  if (compact) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
        <span style={{ fontFamily: "JetBrains Mono, monospace", color: "#71717a",
                       textTransform: "uppercase", letterSpacing: "0.1em", fontSize: 10 }}>
          Model
        </span>
        <select
          style={{ border: "1px solid #e5e5e5", borderRadius: 0, fontSize: 11,
                   padding: "2px 6px", background: "#fff", fontFamily: "IBM Plex Sans, sans-serif" }}
          value={s.llm_mode === "manual" ? s.llm_manual_model : `__tier_${s.llm_tier}`}
          onChange={e => {
            const v = e.target.value;
            if (v.startsWith("__tier_")) {
              onChange({ ...s, llm_mode: "auto", llm_tier: v.replace("__tier_", "") });
            } else {
              onChange({ ...s, llm_mode: "manual", llm_manual_model: v });
            }
          }}
        >
          <optgroup label="── Auto (Smart Router) ──">
            {TIERS.map(t => (
              <option key={t.value} value={`__tier_${t.value}`}>{t.label}</option>
            ))}
          </optgroup>
          {Object.entries(grouped).map(([prov, ms]) => (
            <optgroup key={prov} label={`── ${PROVIDER_BADGE[prov]?.label || prov} ──`}>
              {ms.map(m => (
                <option key={m.id} value={m.id}
                  disabled={!m.key_present && !["lmstudio","ollama"].includes(m.provider)}>
                  {m.label}{!m.key_present && !["lmstudio","ollama"].includes(m.provider)
                    ? " (no key)" : ""}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>
    );
  }

  /* ── Full panel (PathwayConfig page) ── */
  return (
    <div style={{ border: "1px solid #e5e5e5", background: "#fff",
                  padding: 20, fontFamily: "IBM Plex Sans, sans-serif" }}>

      {/* Header */}
      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10,
                    textTransform: "uppercase", letterSpacing: "0.15em",
                    color: "#52525b", marginBottom: 16 }}>
        🧠 AI Model Settings
      </div>

      {/* Mode toggle */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["auto", "manual"].map(mode => (
          <button key={mode} onClick={() => upd("llm_mode", mode)}
            style={{
              flex: 1, padding: "10px 0", fontSize: 12, cursor: "pointer",
              fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.1em",
              textTransform: "uppercase", border: "1px solid",
              background: s.llm_mode === mode ? "#0a0a0a" : "#fff",
              color:      s.llm_mode === mode ? "#fff"    : "#52525b",
              borderColor:s.llm_mode === mode ? "#0a0a0a" : "#e5e5e5",
            }}>
            {mode === "auto" ? "🤖 Auto (Smart)" : "🎛️ Manual (I choose)"}
          </button>
        ))}
      </div>

      {/* AUTO — tier picker */}
      {s.llm_mode === "auto" && (
        <div>
          <div style={{ fontSize: 10, fontFamily: "JetBrains Mono, monospace",
                        textTransform: "uppercase", letterSpacing: "0.12em",
                        color: "#71717a", marginBottom: 10 }}>
            Quality Tier
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {TIERS.map(t => (
              <button key={t.value} onClick={() => upd("llm_tier", t.value)}
                style={{
                  padding: "10px 12px", fontSize: 12, cursor: "pointer", textAlign: "left",
                  border: "1px solid", lineHeight: 1.4,
                  background: s.llm_tier === t.value ? "#0a0a0a" : "#fff",
                  color:      s.llm_tier === t.value ? "#fff"    : "#52525b",
                  borderColor:s.llm_tier === t.value ? "#0a0a0a" : "#e5e5e5",
                }}>
                <div style={{ fontWeight: 700 }}>{t.label}</div>
                <div style={{ fontSize: 10, opacity: 0.7, marginTop: 2 }}>{t.desc}</div>
              </button>
            ))}
          </div>
          <p style={{ fontSize: 11, color: "#71717a", marginTop: 10, lineHeight: 1.5 }}>
            Auto picks <strong>cheap</strong> for resume parsing &amp; scoring,
            <strong> premium</strong> for email drafting.
            Override per-agent below if needed.
          </p>
        </div>
      )}

      {/* MANUAL — single model selector */}
      {s.llm_mode === "manual" && (
        <div>
          <div style={{ fontSize: 10, fontFamily: "JetBrains Mono, monospace",
                        textTransform: "uppercase", letterSpacing: "0.12em",
                        color: "#71717a", marginBottom: 8 }}>
            Model for all agents
          </div>
          {loading ? (
            <div style={{ color: "#71717a", fontSize: 12 }}>Loading models…</div>
          ) : (
            <select
              value={s.llm_manual_model}
              onChange={e => upd("llm_manual_model", e.target.value)}
              style={{ width: "100%", border: "1px solid #0a0a0a", borderRadius: 0,
                       padding: "10px 8px", fontSize: 13,
                       fontFamily: "IBM Plex Sans, sans-serif" }}>
              <option value="">— pick a model —</option>
              {Object.entries(grouped).map(([prov, ms]) => (
                <optgroup key={prov}
                  label={`── ${PROVIDER_BADGE[prov]?.label || prov} ──`}>
                  {ms.map(m => (
                    <option key={m.id} value={m.id}
                      disabled={!m.key_present && !["lmstudio","ollama"].includes(m.provider)}>
                      {m.label}
                      {m.free ? " ✦free" : ""}
                      {!m.key_present && !["lmstudio","ollama"].includes(m.provider)
                        ? "  (add key to .env)" : ""}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          )}

          {/* Provider status legend */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
            {Object.entries(PROVIDER_BADGE).map(([prov, cfg]) => {
              const hasKey = ["lmstudio","ollama"].includes(prov)
                ? true : models.find(m => m.provider === prov)?.key_present;
              return (
                <span key={prov} style={{
                  fontSize: 10, padding: "2px 8px",
                  background: cfg.bg, color: cfg.color,
                  fontFamily: "JetBrains Mono, monospace",
                  border: `1px solid ${cfg.color}22`,
                }}>
                  {cfg.label} {hasKey ? "✓" : "✗ no key"}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Per-agent overrides (advanced) */}
      <div style={{ marginTop: 20, borderTop: "1px solid #f3f4f6", paddingTop: 16 }}>
        <button
          onClick={() => setShowAdvanced(v => !v)}
          style={{ fontSize: 11, background: "none", border: "none", cursor: "pointer",
                   color: "#52525b", fontFamily: "JetBrains Mono, monospace",
                   textTransform: "uppercase", letterSpacing: "0.1em", padding: 0 }}>
          {showAdvanced ? "▼" : "▶"} Per-agent overrides (advanced)
        </button>

        {showAdvanced && (
          <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
            <p style={{ fontSize: 11, color: "#71717a", margin: 0 }}>
              Leave blank to use the global setting above.
              An override here beats everything else for that agent.
            </p>
            {Object.entries(AGENT_LABELS).map(([key, label]) => (
              <div key={key}>
                <div style={{ fontSize: 10, fontFamily: "JetBrains Mono, monospace",
                              textTransform: "uppercase", letterSpacing: "0.1em",
                              color: "#52525b", marginBottom: 4 }}>
                  {label}
                </div>
                <select
                  value={s[key] || ""}
                  onChange={e => upd(key, e.target.value)}
                  style={{ width: "100%", border: "1px solid #e5e5e5", borderRadius: 0,
                           padding: "6px 8px", fontSize: 12,
                           fontFamily: "IBM Plex Sans, sans-serif" }}>
                  <option value="">— inherit from global setting —</option>
                  {Object.entries(grouped).map(([prov, ms]) => (
                    <optgroup key={prov}
                      label={`── ${PROVIDER_BADGE[prov]?.label || prov} ──`}>
                      {ms.map(m => (
                        <option key={m.id} value={m.id}
                          disabled={!m.key_present && !["lmstudio","ollama"].includes(m.provider)}>
                          {m.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
