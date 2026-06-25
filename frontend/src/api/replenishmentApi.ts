import { apiGet } from "./client";
import type {
  ReplenishmentDetail,
  ReplenishmentItem,
} from "../types/replenishment";
import type { ReplenishmentSummary } from "../types/dashboard";

export const replenishmentApi = {
  summary: () => apiGet<ReplenishmentSummary>("/replenishment/summary"),
  suggestions: () =>
    apiGet<ReplenishmentItem[]>("/replenishment/suggestions"),
  critical: () => apiGet<ReplenishmentItem[]>("/replenishment/critical"),
  overstock: () => apiGet<ReplenishmentItem[]>("/replenishment/overstock"),
  item: (itemCode: string) =>
    apiGet<ReplenishmentDetail>(`/replenishment/item/${itemCode}`),
};
