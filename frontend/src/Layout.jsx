import { Link, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analyze", label: "Analyze repository" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-60 shrink-0 border-r border-slate-200 bg-white flex flex-col">
        <div className="px-5 py-5 border-b border-slate-200">
          <p className="font-semibold text-slate-900 text-sm leading-tight">Repo Analyzer</p>
          <p className="text-xs text-slate-500">Viva &amp; interview prep</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.to} to={item.to}
              className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                location.pathname === item.to
                  ? "bg-blue-50 text-blue-700"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-slate-200">
          <p className="text-sm text-slate-700 truncate">{user?.full_name || user?.email}</p>
          <button onClick={logout} className="text-xs text-slate-500 hover:text-blue-600 mt-1">
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
