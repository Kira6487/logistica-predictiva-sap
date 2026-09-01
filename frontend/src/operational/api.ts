import { apiGet } from "../api/client";
import type {
  CoverageRiskSummary,
  DashboardBootstrap,
  ItemDiagnosis,
  PaginatedActionsResponse,
  PaginatedResponse,
  RecommendationActions,
  RecommendationFilters,
  RecommendationItemDetail,
  RecommendationRecord,
  RecommendationsSummary,
  StockSummary,
  WarehouseRecommendationSummary,
} from "./types";

type QueryValue = string | number | boolean | undefined | null;

function buildQuery(params: Record<string, QueryValue> = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "" || value === false) {
      return;
    }
    query.set(key, String(value));
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

async function request<T>(path: string): Promise<T> {
  return apiGet<T>(path);
}

export function getRecommendationsSummary(limit = 5000) {
  return request<RecommendationsSummary>(`/recommendations/summary${buildQuery({ limit })}`);
}

export function getDashboardBootstrap(limit = 5000) {
  return request<DashboardBootstrap>(`/dashboard/bootstrap${buildQuery({ limit })}`);
}

export function getRecommendationsItems(filters: RecommendationFilters = {}) {
  return request<PaginatedResponse<RecommendationRecord>>(`/recommendations/items${buildQuery({ limit: 50, ...filters })}`);
}

export function getRecommendationByItem(itemCode: string) {
  return request<RecommendationItemDetail>(`/recommendations/item/${encodeURIComponent(itemCode)}`);
}

export function getItemDiagnosis(itemCode: string, warehouse?: string) {
  return request<ItemDiagnosis>(`/item-diagnosis/${encodeURIComponent(itemCode)}${buildQuery({ warehouse })}`);
}

export function getRecommendationsWarehouses(limit = 5000) {
  return request<WarehouseRecommendationSummary[]>(`/recommendations/warehouses${buildQuery({ limit })}`);
}

export function getRecommendationsActions(filters: RecommendationFilters = {}) {
  return request<PaginatedActionsResponse>(`/recommendations/actions${buildQuery({ limit: 50, ...filters })}`);
}

export function getPurchaseCandidates(filters: RecommendationFilters = {}) {
  return request<PaginatedResponse<RecommendationRecord>>(`/recommendations/purchase-candidates${buildQuery({ limit: 50, ...filters })}`);
}

export function getTransferCandidates(filters: RecommendationFilters = {}) {
  return request<PaginatedResponse<RecommendationRecord>>(`/recommendations/transfer-candidates${buildQuery({ limit: 50, ...filters })}`);
}

export function getCoverageRiskSummary(limit = 5000) {
  return request<CoverageRiskSummary>(`/coverage-risk/summary${buildQuery({ limit })}`);
}

export function getStockSummary() {
  return request<StockSummary>("/stock/summary");
}
