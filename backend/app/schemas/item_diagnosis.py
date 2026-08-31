from typing import Any

from pydantic import BaseModel


class FormulaLine(BaseModel):
    label: str
    operator: str
    value: float


class AvailabilityAudit(BaseModel):
    stock_disponible: float
    ingresos_esperados: float
    salidas_comprometidas: float
    salidas_proyectadas: float
    stock_seguridad: float
    stock_final_estimado: float
    necesidad_estimada: float
    exceso_estimado: float
    cantidad_sugerida: float
    accion_recomendada: str
    confianza: str
    riesgo: str
    formula_lines: list[FormulaLine]


class ProjectedKardexLine(BaseModel):
    fecha_periodo: str | None
    tipo_movimiento: str
    documento_referencia: str | None
    almacen: str | None
    entrada: float
    salida: float
    saldo_estimado: float
    origen: str
    nota: str | None
    sort_key: str


class RelatedDocument(BaseModel):
    tipo_funcional: str
    numero_documento: str | None
    fecha: str | None
    fecha_esperada: str | None
    socio_negocio: str | None
    almacen: str | None
    cantidad_abierta: float
    estado: str | None


class RelatedDocumentsGroup(BaseModel):
    ingresos_esperados: list[RelatedDocument]
    salidas_comprometidas: list[RelatedDocument]
    produccion_pendiente: list[RelatedDocument]
    traslados_pendientes: list[RelatedDocument]


class ItemDiagnosisItem(BaseModel):
    item_code: str
    item_name: str | None
    warehouse: str | None


class Traceability(BaseModel):
    motivos_recomendacion: list[str]
    motivos_riesgo: list[str]
    notas_calidad_datos: list[str]
    advertencias: list[str]
    formula_resumen: list[FormulaLine]
    mensaje_principal: str
    siguiente_accion: str


class ItemDiagnosis(BaseModel):
    item: ItemDiagnosisItem
    recomendacion_principal: dict[str, Any] | None
    riesgo: str
    confianza: str
    cantidad_sugerida: float
    advertencias: list[str]
    auditoria_disponibilidad: AvailabilityAudit
    kardex_proyectado: list[ProjectedKardexLine]
    documentos_sap_relacionados: RelatedDocumentsGroup
    stock_por_almacen: list[dict[str, Any]]
    trazabilidad: Traceability
