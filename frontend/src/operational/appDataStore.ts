import {
  getCoverageRiskSummary,
  getDashboardBootstrap,
  getItemDiagnosis,
  getPurchaseCandidates,
  getRecommendationsActions,
  getRecommendationsItems,
  getRecommendationsWarehouses,
  getStockSummary,
  getTransferCandidates,
} from "./api";
import type {
  CoverageRiskSummary,
  DashboardBootstrap,
  ItemDiagnosis,
  PaginatedActionsResponse,
  PaginatedResponse,
  RecommendationActions,
  RecommendationFilters,
  RecommendationRecord,
  RecommendationsSummary,
  StockSummary,
  WarehouseRecommendationSummary,
} from "./types";

type ResourceStatus = "idle" | "loading" | "success" | "error";

export interface CachedResource<T> {
  data: T | null;
  status: ResourceStatus;
  error: string | null;
}

export interface AppDataState {
  recommendationsSummary: CachedResource<RecommendationsSummary>;
  recommendationsItems: CachedResource<PaginatedResponse<RecommendationRecord>>;
  recommendationsActions: CachedResource<PaginatedActionsResponse>;
  purchaseCandidates: CachedResource<PaginatedResponse<RecommendationRecord>>;
  transferCandidates: CachedResource<PaginatedResponse<RecommendationRecord>>;
  coverageRiskSummary: CachedResource<CoverageRiskSummary>;
  stockSummary: CachedResource<StockSummary>;
  recommendationsWarehouses: CachedResource<WarehouseRecommendationSummary[]>;
  itemDiagnosisCache: Record<string, CachedResource<ItemDiagnosis>>;
  initialDataLoaded: boolean;
  isLoading: boolean;
  lastUpdated: string | null;
  globalError: string | null;
}

const emptyResource = <T>(): CachedResource<T> => ({ data: null, status: "idle", error: null });

const state: AppDataState = {
  recommendationsSummary: emptyResource(),
  recommendationsItems: emptyResource(),
  recommendationsActions: emptyResource(),
  purchaseCandidates: emptyResource(),
  transferCandidates: emptyResource(),
  coverageRiskSummary: emptyResource(),
  stockSummary: emptyResource(),
  recommendationsWarehouses: emptyResource(),
  itemDiagnosisCache: {},
  initialDataLoaded: false,
  isLoading: false,
  lastUpdated: null,
  globalError: null,
};

const subscribers = new Set<() => void>();
const listCacheKeys = {
  recommendationsItems: "",
  recommendationsActions: "",
  purchaseCandidates: "",
  transferCandidates: "",
};
let initialLoadPromise: Promise<void> | null = null;

function snapshot(): AppDataState {
  return { ...state, itemDiagnosisCache: { ...state.itemDiagnosisCache } };
}

function notify() {
  subscribers.forEach((subscriber) => subscriber());
}

export function subscribeAppData(subscriber: () => void) {
  subscribers.add(subscriber);
  return () => {
    subscribers.delete(subscriber);
  };
}

export function getAppDataSnapshot() {
  return snapshot();
}

function assignResult<T>(resource: CachedResource<T>, result: PromiseSettledResult<T>) {
  if (result.status === "fulfilled") {
    resource.data = result.value;
    resource.status = "success";
    resource.error = null;
  } else {
    resource.status = resource.data ? "success" : "error";
    resource.error = result.reason instanceof Error ? result.reason.message : "No se pudo cargar este bloque.";
  }
}

function summaryFromBootstrap(bootstrap: DashboardBootstrap): RecommendationsSummary {
  return {
    total_recomendaciones_evaluadas: bootstrap.total_recomendaciones_evaluadas,
    total_accion_recomendada: bootstrap.total_accion_recomendada,
    total_requiere_validacion: bootstrap.total_requiere_validacion,
    total_solo_monitoreo: bootstrap.total_solo_monitoreo,
    total_sin_accion: bootstrap.total_sin_accion,
    total_datos_insuficientes: bootstrap.total_datos_insuficientes,
    cantidad_por_tipo: bootstrap.distribucion_por_accion,
    cantidad_por_prioridad: bootstrap.distribucion_por_prioridad,
    cantidad_por_confianza: bootstrap.distribucion_por_confianza,
    compras_sugeridas: bootstrap.compras_sugeridas,
    traslados_sugeridos: bootstrap.traslados_sugeridos,
    validaciones_datos_sugeridas: bootstrap.validaciones_datos_sugeridas,
    revisiones_maestro_sugeridas: bootstrap.revisiones_maestro_sugeridas,
  };
}

function resetLargeLists() {
  state.recommendationsItems = emptyResource();
  state.recommendationsActions = emptyResource();
  state.purchaseCandidates = emptyResource();
  state.transferCandidates = emptyResource();
  listCacheKeys.recommendationsItems = "";
  listCacheKeys.recommendationsActions = "";
  listCacheKeys.purchaseCandidates = "";
  listCacheKeys.transferCandidates = "";
}

export async function loadInitialAppData(force = false) {
  if (state.isLoading && initialLoadPromise) return initialLoadPromise;
  if (state.initialDataLoaded && !force) return Promise.resolve();

  state.isLoading = true;
  state.globalError = null;
  state.recommendationsSummary.status = state.recommendationsSummary.data ? "success" : "loading";
  state.coverageRiskSummary.status = state.coverageRiskSummary.data ? "success" : "loading";
  state.stockSummary.status = state.stockSummary.data ? "success" : "loading";
  state.recommendationsWarehouses.status = state.recommendationsWarehouses.data ? "success" : "loading";
  if (force) resetLargeLists();
  notify();

  initialLoadPromise = Promise.allSettled([
    getDashboardBootstrap(),
    getCoverageRiskSummary(),
    getStockSummary(),
    getRecommendationsWarehouses(),
  ])
    .then((results) => {
      const bootstrap = results[0] as PromiseSettledResult<DashboardBootstrap>;
      if (bootstrap.status === "fulfilled") {
        state.recommendationsSummary.data = summaryFromBootstrap(bootstrap.value);
        state.recommendationsSummary.status = "success";
        state.recommendationsSummary.error = null;
        state.lastUpdated = bootstrap.value.calculado_en;
      } else {
        state.recommendationsSummary.status = state.recommendationsSummary.data ? "success" : "error";
        state.recommendationsSummary.error = bootstrap.reason instanceof Error ? bootstrap.reason.message : "No se pudo cargar el resumen inicial.";
      }
      assignResult(state.coverageRiskSummary, results[1] as PromiseSettledResult<CoverageRiskSummary>);
      assignResult(state.stockSummary, results[2] as PromiseSettledResult<StockSummary>);
      assignResult(state.recommendationsWarehouses, results[3] as PromiseSettledResult<WarehouseRecommendationSummary[]>);
      state.initialDataLoaded = results.some((result) => result.status === "fulfilled") || state.initialDataLoaded;
      state.lastUpdated = state.lastUpdated || new Date().toISOString();
      state.globalError = results.every((result) => result.status === "rejected") ? "No se pudo cargar la informacion inicial." : null;
    })
    .finally(() => {
      state.isLoading = false;
      initialLoadPromise = null;
      notify();
    });

  return initialLoadPromise;
}

function queryKey(filters: RecommendationFilters = {}) {
  return JSON.stringify(Object.entries(filters).sort(([a], [b]) => a.localeCompare(b)));
}

async function loadPage<T>(
  resource: CachedResource<T>,
  cacheKeyName: keyof typeof listCacheKeys,
  key: string,
  loader: () => Promise<T>,
  force = false,
) {
  if (resource.status === "loading" && !force) return resource.data;
  if (resource.data && listCacheKeys[cacheKeyName] === key && !force) return resource.data;
  resource.status = resource.data ? "success" : "loading";
  resource.error = null;
  notify();
  try {
    const data = await loader();
    resource.data = data;
    resource.status = "success";
    resource.error = null;
    listCacheKeys[cacheKeyName] = key;
    notify();
    return data;
  } catch (error) {
    resource.status = resource.data ? "success" : "error";
    resource.error = error instanceof Error ? error.message : "No se pudo cargar esta pagina.";
    notify();
    return resource.data;
  }
}

export function loadRecommendationsPage(filters: RecommendationFilters = {}, force = false) {
  const key = queryKey(filters);
  return loadPage(state.recommendationsItems, "recommendationsItems", key, () => getRecommendationsItems(filters), force);
}

export function loadPurchaseCandidatesPage(filters: RecommendationFilters = {}, force = false) {
  const key = queryKey(filters);
  return loadPage(state.purchaseCandidates, "purchaseCandidates", key, () => getPurchaseCandidates(filters), force);
}

export function loadTransferCandidatesPage(filters: RecommendationFilters = {}, force = false) {
  const key = queryKey(filters);
  return loadPage(state.transferCandidates, "transferCandidates", key, () => getTransferCandidates(filters), force);
}

export function loadActionsPage(filters: RecommendationFilters = {}, force = false) {
  const key = queryKey(filters);
  return loadPage(state.recommendationsActions, "recommendationsActions", key, () => getRecommendationsActions(filters), force);
}

function diagnosisKey(itemCode: string, warehouse?: string) {
  return `${itemCode.trim()}::${warehouse?.trim() || ""}`;
}

export async function loadItemDiagnosis(itemCode: string, warehouse?: string, force = false) {
  const key = diagnosisKey(itemCode, warehouse);
  const existing = state.itemDiagnosisCache[key];
  if (existing && existing.status === "success" && !force) return existing.data;
  if (existing && existing.status === "loading" && !force) return existing.data;

  state.itemDiagnosisCache[key] = {
    data: existing?.data || null,
    status: existing?.data ? "success" : "loading",
    error: null,
  };
  notify();

  try {
    const data = await getItemDiagnosis(itemCode, warehouse);
    state.itemDiagnosisCache[key] = { data, status: "success", error: null };
    notify();
    return data;
  } catch (error) {
    state.itemDiagnosisCache[key] = {
      data: existing?.data || null,
      status: existing?.data ? "success" : "error",
      error: error instanceof Error ? error.message : "No se pudo cargar el diagnostico.",
    };
    notify();
    return existing?.data || null;
  }
}

export function getCachedItemDiagnosis(itemCode: string, warehouse?: string) {
  return state.itemDiagnosisCache[diagnosisKey(itemCode, warehouse)] || emptyResource<ItemDiagnosis>();
}
