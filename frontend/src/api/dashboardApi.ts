import { apiGet } from "./client";
import type { HealthResponse, ReplenishmentSummary } from "../types/dashboard";
import type { AnalyticsSummary } from "../types/analytics";
import type { ForecastSummary } from "../types/forecast";

export const dashboardApi = {
  health: () => apiGet<HealthResponse>("/api/health"),
  replenishment: () =>
    apiGet<ReplenishmentSummary>("/replenishment/summary"),
  forecast: () => apiGet<ForecastSummary>("/forecast/summary"),
  analytics: () => apiGet<AnalyticsSummary>("/analytics/summary"),
};
