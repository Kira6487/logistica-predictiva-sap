from typing import Any

from pydantic import BaseModel

from app.schemas.coverage_risk import CoverageRiskItemDetail, CoverageRiskRecord
from app.schemas.inventory_position import OpenDocumentRecord, StockPositionRecord


class PurchaseEnrichment(BaseModel):
    preferred_vendor_code: str | None
    preferred_vendor_name: str | None
    item_group_code: str | None
    item_group_name: str | None
    estimated_lead_time_days: float | None
    last_purchase_date: str | None
    last_purchase_vendor: str | None
    last_purchase_price: float | None
    min_stock: float | None
    max_stock: float | None
    min_purchase_qty: float | None
    purchase_multiple: float | None


class RecommendationRecord(CoverageRiskRecord):
    recommendation_type: str
    recommendation_status: str
    priority_level: str
    priority_score: float
    priority_reasons: list[str]
    suggested_quantity: float
    suggested_quantity_30d: float
    suggested_quantity_60d: float
    suggested_quantity_90d: float
    suggested_horizon_days: int | None
    requires_human_approval: bool
    recommendation_confidence: str | None
    recommendation_warning: str
    preferred_vendor_code: str | None
    preferred_vendor_name: str | None
    item_group_code: str | None
    item_group_name: str | None
    estimated_lead_time_days: float | None
    last_purchase_date: str | None
    last_purchase_vendor: str | None
    last_purchase_price: float | None
    min_stock: float | None
    max_stock: float | None
    min_purchase_qty: float | None
    purchase_multiple: float | None
    demand_during_lead_time: float | None
    coverage_after_lead_time: float | None
    lead_time_risk: str
    source_warehouse: str | None
    target_warehouse: str | None
    transfer_candidate_quantity: float
    source_projected_stock_before_transfer: float | None
    target_projected_stock_before_transfer: float | None
    source_remaining_stock_after_transfer: float | None
    target_projected_stock_after_transfer: float | None
    transfer_reason: str | None
    main_message: str
    recommendation_detail: str
    business_reason: str
    technical_reason: str
    data_quality_notes: list[str]
    next_action_label: str
    next_action_description: str


class RecommendationSummary(BaseModel):
    total_recomendaciones_evaluadas: int
    total_accion_recomendada: int
    total_requiere_validacion: int
    total_solo_monitoreo: int
    total_sin_accion: int
    total_datos_insuficientes: int
    cantidad_por_tipo: dict[str, int]
    cantidad_por_prioridad: dict[str, int]
    cantidad_por_confianza: dict[str, int]
    compras_sugeridas: int
    traslados_sugeridos: int
    validaciones_datos_sugeridas: int
    revisiones_maestro_sugeridas: int


class RecommendationItemDetail(BaseModel):
    item_code: str
    item_name: str | None
    recommendations_by_warehouse: list[RecommendationRecord]
    coverage_diagnosis: CoverageRiskItemDetail
    stock_by_warehouse: list[StockPositionRecord]
    monthly_consumption: list[dict[str, Any]]
    open_documents: list[OpenDocumentRecord]
    purchase_enrichment: PurchaseEnrichment
    summary: RecommendationSummary


class RecommendationWarehouseSummary(BaseModel):
    warehouse_code: str | None
    warehouse_name: str | None
    recomendaciones_urgentes: int
    recomendaciones_altas: int
    compras_sugeridas: int
    traslados_sugeridos: int
    validaciones_datos: int
    articulos_sin_accion: int


class RecommendationActions(BaseModel):
    compras_sugeridas: list[RecommendationRecord]
    traslados_sugeridos: list[RecommendationRecord]
    oc_abiertas_a_acelerar: list[RecommendationRecord]
    ov_a_revisar: list[RecommendationRecord]
    articulos_para_validar_datos: list[RecommendationRecord]
    articulos_para_revisar_maestro: list[RecommendationRecord]


class PaginatedRecommendations(BaseModel):
    items: list[RecommendationRecord]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class PaginatedRecommendationActions(BaseModel):
    items: RecommendationActions
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class PurchaseEnrichmentSourceDiagnostic(BaseModel):
    source: str
    type: str | None
    exists: bool
    description: str
    columns: list[str]
    candidate_columns_found: list[str]
    missing_candidate_columns: list[str]
