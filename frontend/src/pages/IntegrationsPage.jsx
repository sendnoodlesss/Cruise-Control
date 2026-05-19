import { useEffect, useState } from "react";
import { getIntegrationsStatus } from "../lib/api";

export default function IntegrationsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getIntegrationsStatus()
      .then(setData)
      .catch(() => {});
  }, []);

  function renderCard(name, value) {
    return (
      <div className="bg-white brutal-border p-5">
        <div className="font-display text-2xl font-bold mb-2">{name}</div>
        <div className="text-sm text-zinc-600">
          {value?.connected ? "Connected" : "Not connected"}
        </div>
        {value?.stub && (
          <div className="mt-2 text-xs text-zinc-500">
            Currently backend stub. Real OAuth can be wired next.
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="label-caps mb-2">Integrations</div>
      <h1 className="font-display text-5xl font-black leading-none m-0">
        Workspace Integrations
      </h1>
      <p className="mt-3 text-zinc-600 max-w-3xl">
        Gmail, Sheets, and Calendar status are shown here.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        {renderCard("Gmail", data?.gmail)}
        {renderCard("Sheets", data?.sheets)}
        {renderCard("Calendar", data?.calendar)}
      </div>
    </div>
  );
}