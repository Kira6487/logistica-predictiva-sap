import { Navigate, Route, Routes } from "react-router-dom";
import { PortalLayout } from "./layouts/PortalLayout";
import { AdvancedAnalysisPage } from "./pages/AdvancedAnalysisPage";
import { HomePage } from "./pages/HomePage";
import { ItemDiagnosisPage } from "./pages/ItemDiagnosisPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<PortalLayout />}>
        <Route index element={<Navigate to="/inicio" replace />} />
        <Route path="/inicio" element={<HomePage />} />
        <Route path="/recomendaciones" element={<RecommendationsPage />} />
        <Route path="/diagnostico-articulo" element={<ItemDiagnosisPage />} />
        <Route path="/analisis-avanzado" element={<AdvancedAnalysisPage />} />
        <Route path="/dashboard" element={<Navigate to="/inicio" replace />} />
        <Route path="/replenishment" element={<Navigate to="/recomendaciones" replace />} />
        <Route path="/critical" element={<Navigate to="/recomendaciones" replace />} />
        <Route path="/overstock" element={<Navigate to="/recomendaciones" replace />} />
        <Route path="/forecast" element={<Navigate to="/analisis-avanzado" replace />} />
        <Route path="/abc-xyz" element={<Navigate to="/analisis-avanzado" replace />} />
        <Route path="/inventory" element={<Navigate to="/analisis-avanzado" replace />} />
        <Route path="/interpretation" element={<Navigate to="/inicio" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/inicio" replace />} />
    </Routes>
  );
}
