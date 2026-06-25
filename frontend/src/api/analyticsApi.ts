import { apiGet } from "./client";
import type { AnalyticsItem, AnalyticsSummary } from "../types/analytics";

export const analyticsApi = {
  summary: () => apiGet<AnalyticsSummary>("/analytics/summary"),
  abc: () => apiGet<AnalyticsItem[]>("/analytics/abc"),
  xyz: () => apiGet<AnalyticsItem[]>("/analytics/xyz"),
  combined: () => apiGet<AnalyticsItem[]>("/analytics/abc-xyz"),
};
