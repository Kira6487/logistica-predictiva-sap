from pydantic import BaseModel


class DashboardBootstrap(BaseModel):
    total_recomendaciones_evaluadas: int
    total_accion_recomendada: int
    total_requiere_validacion: int
    total_solo_monitoreo: int
    total_sin_accion: int
    total_datos_insuficientes: int
    compras_sugeridas: int
    traslados_sugeridos: int
    validaciones_datos_sugeridas: int
    revisiones_maestro_sugeridas: int
    distribucion_por_accion: dict[str, int]
    distribucion_por_prioridad: dict[str, int]
    distribucion_por_confianza: dict[str, int]
    distribucion_por_estado: dict[str, int]
    calculado_en: str
