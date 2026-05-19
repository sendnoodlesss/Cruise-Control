import { NavLink, Outlet } from "react-router-dom";

const baseClass =
  "flex items-center gap-2 px-4 py-3 text-sm border-b border-zinc-800";
const getNavClass = ({ isActive }) =>
  `${baseClass} ${isActive ? "bg-white text-black font-semibold" : "text-zinc-300"}`;

export default function Shell() {
  return (
    <div className="min-h-screen bg-[#fafafa] text-[#0a0a0a] flex">
      <aside className="w-[260px] bg-[#0b0b0b] text-white min-h-screen flex flex-col justify-between border-r border-zinc-800">
        <div>
          <div className="px-5 py-6 border-b border-zinc-800">
            <div className="font-display text-[28px] font-black tracking-tight">
              Cruise Control
            </div>
            <div className="mt-1 text-xs text-zinc-400 font-mono">
              Agent Internship Hunter
            </div>
          </div>

          <nav className="pt-3">
            <NavLink to="/dashboard" className={getNavClass}>
              <span>📊</span>
              <span>Dashboard</span>
            </NavLink>

            <NavLink to="/pathways/new" className={getNavClass}>
              <span>＋</span>
              <span>New Pathway</span>
            </NavLink>

            <NavLink to="/apis" className={getNavClass}>
              <span>🔌</span>
              <span>APIs</span>
            </NavLink>

            <NavLink to="/integrations" className={getNavClass}>
              <span>🧩</span>
              <span>Integrations</span>
            </NavLink>
          </nav>
        </div>

        <div className="px-5 py-4 border-t border-zinc-800 text-xs text-zinc-500 font-mono">
          v1.0 · local build
        </div>
      </aside>

      <main className="flex-1 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}