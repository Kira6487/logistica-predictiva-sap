import {
  Boxes,
  ChartColumnIncreasing,
  ClipboardList,
  House,
  SearchCheck,
} from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const navigation = [
  { to: "/inicio", label: "Inicio", icon: House },
  { to: "/recomendaciones", label: "Recomendaciones", icon: ClipboardList },
  { to: "/diagnostico-articulo", label: "Diagnóstico por artículo", icon: SearchCheck },
  { to: "/analisis-avanzado", label: "Análisis avanzado", icon: ChartColumnIncreasing },
];

export function PortalLayout() {
  const location = useLocation();
  const active = navigation.find((item) => location.pathname.startsWith(item.to));

  return (
    <div className="portal-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Boxes size={24} />
          </div>
          <div>
            <strong>Logística Predictiva</strong>
            <span>SAP Business One</span>
          </div>
        </div>
        <nav>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="connection-dot" />
          <div>
            <strong>Entorno local</strong>
            <span>SAP en solo lectura</span>
          </div>
        </div>
      </aside>
      <div className="portal-main">
        <header className="topbar">
          <div>
            <span className="eyebrow">Portal de Logística Predictiva</span>
            <h1>{active?.label || "Inicio"}</h1>
          </div>
          <div className="topbar-meta">
            <span>Horizonte operativo</span>
            <strong>3 meses</strong>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
