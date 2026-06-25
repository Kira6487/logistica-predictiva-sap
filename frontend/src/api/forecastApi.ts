import { apiGet } from "./client";
import type {
  ForecastCandidate,
  ForecastItemDetail,
  ForecastResultPoint,
  ForecastSummary,
} from "../types/forecast";

export const forecastApi = {
  summary: () => apiGet<ForecastSummary>("/forecast/summary"),
  candidates: () => apiGet<ForecastCandidate[]>("/forecast/candidates"),
  results: () => apiGet<ForecastResultPoint[]>("/forecast/results"),
  item: (itemCode: string) =>
    apiGet<ForecastItemDetail>(`/forecast/item/${itemCode}`),
};
