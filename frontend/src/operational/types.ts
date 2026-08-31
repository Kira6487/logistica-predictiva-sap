export type SummaryMap = Record<string, number>;

export interface RecommendationsSummary {
  total_recomendaciones_evaluadas: number;
  total_accion_recomendada: number;
  total_requiere_validacion: number;
  total_solo_monitoreo: number;
  total_sin_accion: number;
  total_datos_insuficientes: number;
  cantidad_por_tipo: SummaryMap;
  cantidad_por_prioridad: SummaryMap;
  cantidad_por_confianza: SummaryMap;
  compras_sugeridas: number;
  traslados_sugeridos: number;
  validaciones_datos_sugeridas: number;
  revisiones_maestro_sugeridas: number;
}

export interface DashboardBootstrap {
  total_recomendaciones_evaluadas: number;
  total_accion_recomendada: number;
  total_requiere_validacion: number;
  total_solo_monitoreo: number;
  total_sin_accion: number;
  total_datos_insuficientes: number;
  compras_sugeridas: number;
  traslados_sugeridos: number;
  validaciones_datos_sugeridas: number;
  revisiones_maestro_sugeridas: number;
  distribucion_por_accion: SummaryMap;
  distribucion_por_prioridad: SummaryMap;
  distribucion_por_confianza: SummaryMap;
  distribucion_por_estado: SummaryMap;
  calculado_en: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedActionsResponse {
  items: RecommendationActions;
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface CoverageRiskSummary {
  total_articulos_evaluados: number;
  total_combinaciones_evaluadas: number;
  riesgo_critico: number;
  riesgo_alto: number;
  riesgo_medio: number;
  riesgo_bajo: number;
  sin_diagnostico: number;
  sin_riesgo_aparente: number;
  confianza_alta: number;
  confianza_media: number;
  confianza_baja: number;
  sin_confianza: number;
}

export interface StockSummary {
  total_items_with_stock: number;
  total_warehouses: number;
  stock_fisico_total: number;
  stock_disponible_total: number;
  items_without_stock: number;
  negative_stock_items: number;
  committed_over_stock_items: number;
  items_with_open_orders: number;
}

export interface RecommendationRecord {
  item_code: string | null;
  item_name: string | null;
  warehouse_code: string | null;
  warehouse_name: string | null;
  recommendation_type: string;
  recommendation_status: string;
  priority_level: string;
  priority_score: number;
  priority_reasons: string[];
  nivel_riesgo: string;
  nivel_confianza: string;
  main_message: string;
  recommendation_detail: string;
  business_reason: string;
  technical_reason: string;
  data_quality_notes: string[];
  next_action_label: string;
  next_action_description: string;
  suggested_quantity: number;
  suggested_quantity_30d: number;
  suggested_quantity_60d: number;
  suggested_quantity_90d: number;
  suggested_horizon_days: number | null;
  recommendation_warning: string;
  recommendation_confidence: string | null;
  requires_human_approval: boolean;
  preferred_vendor_code: string | null;
  preferred_vendor_name: string | null;
  estimated_lead_time_days: number | null;
  last_purchase_date: string | null;
  last_purchase_vendor: string | null;
  last_purchase_price: number | null;
  source_warehouse: string | null;
  target_warehouse: string | null;
  transfer_candidate_quantity: number;
  source_projected_stock_before_transfer: number | null;
  target_projected_stock_before_transfer: number | null;
  source_remaining_stock_after_transfer: number | null;
  target_projected_stock_after_transfer: number | null;
  transfer_reason: string | null;
}

export interface RecommendationActions {
  compras_sugeridas: RecommendationRecord[];
  traslados_sugeridos: RecommendationRecord[];
  oc_abiertas_a_acelerar: RecommendationRecord[];
  ov_a_revisar: RecommendationRecord[];
  articulos_para_validar_datos: RecommendationRecord[];
  articulos_para_revisar_maestro: RecommendationRecord[];
}

export interface WarehouseRecommendationSummary {
  warehouse_code: string | null;
  warehouse_name: string | null;
  recomendaciones_urgentes: number;
  recomendaciones_altas: number;
  compras_sugeridas: number;
  traslados_sugeridos: number;
  validaciones_datos: number;
  articulos_sin_accion: number;
}

export interface RecommendationItemDetail {
  item_code: string;
  item_name: string | null;
  recommendations_by_warehouse: RecommendationRecord[];
  coverage_diagnosis: {
    diagnostics_by_warehouse: Array<Record<string, unknown>>;
    open_documents: Array<Record<string, unknown>>;
    monthly_consumption: Array<Record<string, unknown>>;
  };
  stock_by_warehouse: Array<Record<string, unknown>>;
  open_documents: Array<Record<string, unknown>>;
  monthly_consumption: Array<Record<string, unknown>>;
  purchase_enrichment: Record<string, unknown>;
  summary: RecommendationsSummary;
}

export interface FormulaLine {
  label: string;
  operator: string;
  value: number;
}

export interface AvailabilityAudit {
  stock_disponible: number;
  ingresos_esperados: number;
  salidas_comprometidas: number;
  salidas_proyectadas: number;
  stock_seguridad: number;
  stock_final_estimado: number;
  necesidad_estimada: number;
  exceso_estimado: number;
  cantidad_sugerida: number;
  accion_recomendada: string;
  confianza: string;
  riesgo: string;
  formula_lines: FormulaLine[];
}

export interface ProjectedKardexLine {
  fecha_periodo: string | null;
  tipo_movimiento: string;
  documento_referencia: string | null;
  almacen: string | null;
  entrada: number;
  salida: number;
  saldo_estimado: number;
  origen: "SAP real" | "SAP abierto" | "Proyección" | "Diagnóstico" | "Recomendación" | string;
  nota: string | null;
  sort_key: string;
}

export interface RelatedDocument {
  tipo_funcional: string;
  numero_documento: string | null;
  fecha: string | null;
  fecha_esperada: string | null;
  socio_negocio: string | null;
  almacen: string | null;
  cantidad_abierta: number;
  estado: string | null;
}

export interface RelatedDocumentsGroup {
  ingresos_esperados: RelatedDocument[];
  salidas_comprometidas: RelatedDocument[];
  produccion_pendiente: RelatedDocument[];
  traslados_pendientes: RelatedDocument[];
}

export interface ItemDiagnosis {
  item: {
    item_code: string;
    item_name: string | null;
    warehouse: string | null;
  };
  recomendacion_principal: RecommendationRecord | null;
  riesgo: string;
  confianza: string;
  cantidad_sugerida: number;
  advertencias: string[];
  auditoria_disponibilidad: AvailabilityAudit;
  kardex_proyectado: ProjectedKardexLine[];
  documentos_sap_relacionados: RelatedDocumentsGroup;
  stock_por_almacen: Array<Record<string, unknown>>;
  trazabilidad: {
    motivos_recomendacion: string[];
    motivos_riesgo: string[];
    notas_calidad_datos: string[];
    advertencias: string[];
    formula_resumen: FormulaLine[];
    mensaje_principal: string;
    siguiente_accion: string;
  };
}

export interface RecommendationFilters {
  item_code?: string;
  warehouse?: string;
  recommendation_type?: string;
  recommendation_status?: string;
  priority_level?: string;
  risk_level?: string;
  confidence_level?: string;
  only_actionable?: boolean;
  only_purchase_suggestions?: boolean;
  only_transfer_suggestions?: boolean;
  only_data_validation?: boolean;
  only_master_review?: boolean;
  min_priority_score?: number;
  max_priority_score?: number;
  offset?: number;
  page?: number;
  page_size?: number;
  limit?: number;
}
