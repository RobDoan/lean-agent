import { Link, NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }): string =>
  isActive
    ? "underline underline-offset-4 font-medium"
    : "hover:underline underline-offset-4";

export function TopNav() {
  return (
    <header className="flex items-center justify-between border-b px-6 py-3">
      <Link to="/" className="font-semibold hover:underline">lean-agent</Link>
      <nav className="flex gap-6 text-sm">
        <NavLink to="/" end className={linkClass}>
          Dashboard
        </NavLink>
        <NavLink to="/personas" className={linkClass}>
          Personas
        </NavLink>
        <NavLink to="/panel-presets" className={linkClass}>
          Panel Presets
        </NavLink>
      </nav>
    </header>
  );
}
