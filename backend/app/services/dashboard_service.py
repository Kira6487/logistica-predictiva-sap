from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.recommendation_service import get_recommendations_summary


def get_dashboard_bootstrap(limit: int = 5000) -> dict[str, Any]:
    summary = get_recommendations_summary(limit=limit)
    return {
        "total_recomendaciones_evaluadas": summary["total_recomendaciones_evaluadas"],
        "total_accion_recomendada": summary["total_accion_recomendada"],
        "total_requiere_validacion": summary["total_requiere_validacion"],
        "total_solo_monitoreo": summary["total_solo_monitoreo"],
        "total_sin_accion": summary["total_sin_accion"],
        "total_datos_insuficientes": summary["total_datos_insuficientes"],
        "compras_sugeridas": summary["compras_sugeridas"],
        "traslados_sugeridos": summary["traslados_sugeridos"],
        "validaciones_datos_sugeridas": summary["validaciones_datos_sugeridas"],
        "revisiones_maestro_sugeridas": summary["revisiones_maestro_sugeridas"],
        "distribucion_por_accion": summary["cantidad_por_tipo"],
        "distribucion_por_prioridad": summary["cantidad_por_prioridad"],
        "distribucion_por_confianza": summary["cantidad_por_confianza"],
        "distribucion_por_estado": {
            "accion_recomendada": summary["total_accion_recomendada"],
            "requiere_validacion": summary["total_requiere_validacion"],
            "solo_monitoreo": summary["total_solo_monitoreo"],
            "no_accion": summary["total_sin_accion"],
            "datos_insuficientes": summary["total_datos_insuficientes"],
        },
        "calculado_en": datetime.now(timezone.utc).isoformat(),
    }
