import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getEmailDrafts,
  updateEmail,
  removeEmail,
  sendEmails,
} from "../lib/api";

export default function EmailReview() {
  const { id } = useParams();
  const [drafts, setDrafts] = useState([]);
  const [selected, setSelected] = useState(null);

  async function load() {
    try {
      const data = await getEmailDrafts(id);
      setDrafts(data);
      if (data.length > 0 && !selected) {
        setSelected(data[0]);
      }
    } catch (error) {
      console.error("Failed to load drafts", error);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function saveCurrent() {
    if (!selected) return;
    await updateEmail(selected.id, {
      subject: selected.subject,
      body: selected.body,
    });
    await load();
  }

  async function removeCurrent() {
    if (!selected) return;
    await removeEmail(selected.id);
    setSelected(null);
    await load();
  }

  async function sendCurrent() {
    if (!selected) return;
    await sendEmails(id, [selected.id]);
    await load();
  }

  return (
    <div className="p-8">
      <div className="label-caps mb-2">Email Review</div>
      <h1 className="font-display text-5xl font-black leading-none m-0">
        Drafted Outreach
      </h1>

      <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-6 mt-8">
        <div className="bg-white brutal-border">
          <div className="px-5 py-4 brutal-border border-x-0 border-t-0 font-display text-2xl font-bold">
            Draft List
          </div>

          <div className="p-3 space-y-2">
            {drafts.length > 0 ? (
              drafts.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelected(d)}
                  className={`w-full text-left brutal-border p-3 ${
                    selected?.id === d.id ? "bg-black text-white" : "bg-white"
                  }`}
                >
                  <div className="font-semibold text-sm">{d.company_name}</div>
                  <div className="text-xs opacity-80 mt-1">{d.email_to}</div>
                  <div className="text-xs opacity-80 mt-2 line-clamp-2">
                    {d.subject}
                  </div>
                </button>
              ))
            ) : (
              <div className="text-zinc-500 p-3">No drafts yet.</div>
            )}
          </div>
        </div>

        <div className="bg-white brutal-border p-6">
          {selected ? (
            <>
              <div className="mb-4">
                <label className="block text-sm font-semibold mb-2">To</label>
                <input
                  className="w-full brutal-border p-3 bg-zinc-50"
                  value={selected.email_to || ""}
                  readOnly
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-semibold mb-2">
                  Subject
                </label>
                <input
                  className="w-full brutal-border p-3"
                  value={selected.subject || ""}
                  onChange={(e) =>
                    setSelected({ ...selected, subject: e.target.value })
                  }
                />
              </div>

              <div className="mb-5">
                <label className="block text-sm font-semibold mb-2">Body</label>
                <textarea
                  className="w-full brutal-border p-3 min-h-[320px]"
                  value={selected.body || ""}
                  onChange={(e) =>
                    setSelected({ ...selected, body: e.target.value })
                  }
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={saveCurrent}
                  className="px-4 py-3 brutal-border bg-white text-sm font-semibold"
                >
                  Save Draft
                </button>
                <button
                  onClick={removeCurrent}
                  className="px-4 py-3 brutal-border bg-white text-sm font-semibold"
                >
                  Remove
                </button>
                <button
                  onClick={sendCurrent}
                  className="px-5 py-3 bg-black text-white text-sm font-semibold"
                >
                  Send via Gmail
                </button>
              </div>
            </>
          ) : (
            <div className="text-zinc-500">Select a draft from the left.</div>
          )}
        </div>
      </div>
    </div>
  );
}