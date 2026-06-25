import {
  BarChart3,
  Boxes,
  ChartNoAxesCombined,
  CircleHelp,
  Gauge,
  PackageSearch,
  ShieldAlert,
  ShoppingCart,
  Warehouse,
} from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/replenishment", label: "Reposición sugerida", icon: ShoppingCart },
  { to: "/critical", label: "Productos críticos", icon: ShieldAlert },
  { to: "/overstock", label: "Sobrestock", icon: PackageSearch },
  { to: "/forecast", label: "Forecast", icon: ChartNoAxesCombined },
  { to: "/abc-xyz", label: "ABC / XYZ", icon: BarChart3 },
  { to: "/inventory", label: "Inventario", icon: Warehouse },
  { to: "/interpretation", label: "Interpretación", icon: CircleHelp },
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
            <h1>{active?.label || "Dashboard"}</h1>
          </div>
          <div className="topbar-meta">
            <span>Horizonte operativo</span>
            <strong>Ene–Mar 2026</strong>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
