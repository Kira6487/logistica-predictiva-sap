from typing import Any

from pydantic import BaseModel

from app.schemas.inventory_position import InventoryPositionRecord, OpenDocumentRecord, StockPositionRecord


class CoverageRiskRecord(InventoryPositionRecord):
    consumo_total_historico: float
    periodos_historicos_detectados: int
    meses_con_consumo: int
    meses_sin_consumo: int
    fecha_ultimo_consumo: str | None
    consumo_promedio_mensual_3m: float
    consumo_promedio_mensual_6m: float
    consumo_promedio_mensual_12m: float
    consumo_promedio_mensual_general: float
    consumo_mediano_mensual: float
    consumo_maximo_mensual: float
    consumo_minimo_mensual: float
    desviacion_consumo_mensual: float
    coeficiente_variacion: float
    ratio_meses_con_consumo: float
    tipo_demanda: str
    consumo_base_mensual: float
    consumo_base_diario: float
    fuente_consumo_base: str
    cobertura_dias_stock_disponible: float | None
    cobertura_dias_stock_proyectado: float | None
    cobertura_meses_stock_disponible: float | None
    cobertura_meses_stock_proyectado: float | None
    deficit_30_dias: float
    deficit_60_dias: float
    deficit_90_dias: float
    sobrante_30_dias: float
    sobrante_60_dias: float
    sobrante_90_dias: float
    nivel_riesgo: str
    nivel_confianza: str
    motivo_confianza: str
    motivos_riesgo: list[str]


class CoverageRiskSummary(BaseModel):
    total_articulos_evaluados: int
    total_combinaciones_evaluadas: int
    riesgo_critico: int
    riesgo_alto: int
    riesgo_medio: int
    riesgo_bajo: int
    sin_diagnostico: int
    sin_riesgo_aparente: int
    confianza_alta: int
    confianza_media: int
    confianza_baja: int
    sin_confianza: int
    articulos_stock_disponible_negativo: int
    articulos_comprometido_mayor_stock: int
    articulos_deficit_30_dias: int
    articulos_deficit_60_dias: int
    articulos_deficit_90_dias: int
    almacenes_consumo_sin_stock_actual: int
    almacenes_stock_sin_consumo_historico: int


class CoverageRiskItemDetail(BaseModel):
    item_code: str
    item_name: str | None
    diagnostics_by_warehouse: list[CoverageRiskRecord]
    stock_by_warehouse: list[StockPositionRecord]
    monthly_consumption: list[dict[str, Any]]
    open_documents: list[OpenDocumentRecord]
    summary: CoverageRiskSummary


class CoverageRiskWarehouseSummary(BaseModel):
    warehouse_code: str | None
    warehouse_name: str | None
    articulos_evaluados: int
    criticos: int
    altos: int
    medios: int
    bajos: int
    sin_diagnostico: int
    deficit_total_30_dias: float
    deficit_total_60_dias: float
    deficit_total_90_dias: float
    articulos_sin_stock_con_consumo: int


class CoverageReconciliation(BaseModel):
    almacenes_consumo_sin_stock_actual: list[str]
    almacenes_stock_sin_consumo_historico: list[str]
    articulos_consumo_sin_stock_actual: list[str]
    articulos_stock_sin_consumo_historico: list[str]
    articulos_partidas_abiertas_sin_consumo_historico: list[str]
    articulos_partidas_abiertas_sin_stock_actual: list[str]
    total_combinaciones_consumo: int
    total_combinaciones_stock: int
    total_combinaciones_partidas_abiertas: int
