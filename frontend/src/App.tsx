import { Navigate, Route, Routes } from "react-router-dom";
import { PortalLayout } from "./layouts/PortalLayout";
import { AbcXyzPage } from "./pages/AbcXyzPage";
import { CriticalItemsPage } from "./pages/CriticalItemsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ForecastPage } from "./pages/ForecastPage";
import { InterpretationPage } from "./pages/InterpretationPage";
import { InventoryPage } from "./pages/InventoryPage";
import { OverstockPage } from "./pages/OverstockPage";
import { ReplenishmentPage } from "./pages/ReplenishmentPage";

export default function App() {
  return (
    <Routes>
      <Route element={<PortalLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/replenishment" element={<ReplenishmentPage />} />
        <Route path="/critical" element={<CriticalItemsPage />} />
        <Route path="/overstock" element={<OverstockPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/abc-xyz" element={<AbcXyzPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/interpretation" element={<InterpretationPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
