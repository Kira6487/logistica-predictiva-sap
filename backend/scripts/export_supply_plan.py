from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.recommendation_service import get_recommendation_items  # noqa: E402


def _action_label(record: dict[str, Any]) -> str:
    recommendation_type = record.get("recommendation_type")
    risk = record.get("nivel_riesgo")
    if recommendation_type == "comprar" and risk == "critico":
        return "Atender riesgo crítico"
    if recommendation_type in {"comprar", "acelerar_compra_abierta"}:
        return "Abastecer ahora"
    if recommendation_type in {"trasladar_stock", "revisar_venta_comprometida"}:
        return "Revisar antes de abastecer"
    if recommendation_type == "no_comprar":
        return "No comprar"
    if recommendation_type == "validar_datos":
        return "Validar datos"
    if recommendation_type == "revisar_maestro_articulo":
        return "Revisar maestro"
    return "Monitorear"


def _safe_next_action(record: dict[str, Any]) -> str:
    recommendation_type = record.get("recommendation_type")
    if recommendation_type in {"comprar", "trasladar_stock"}:
        return "Validar con logística"
    if recommendation_type in {"acelerar_compra_abierta", "revisar_venta_comprometida"}:
        return "Revisar documentos"
    if recommendation_type == "validar_datos":
        return "Validar datos"
    if recommendation_type == "revisar_maestro_articulo":
        return "Revisar maestro"
    return "Monitorear"


def _row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "artículo": record.get("item_name") or record.get("item_code"),
        "almacén": record.get("warehouse_code"),
        "acción recomendada": _action_label(record),
        "cantidad sugerida": record.get("suggested_quantity"),
        "prioridad": record.get("priority_level"),
        "confianza": record.get("recommendation_confidence") or record.get("nivel_confianza"),
        "riesgo": record.get("nivel_riesgo"),
        "motivo": record.get("business_reason") or record.get("main_message"),
        "siguiente acción": _safe_next_action(record),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta el plan funcional de abastecimiento.")
    parser.add_argument("--item-code", default=None)
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--priority-level", default=None)
    parser.add_argument("--risk-level", default=None)
    parser.add_argument("--confidence-level", default=None)
    parser.add_argument("--limit", type=int, default=250000)
    parser.add_argument("--output", default=str(BACKEND_DIR / "exports" / "plan_abastecimiento.csv"))
    args = parser.parse_args()

    rows = get_recommendation_items(
        item_code=args.item_code,
        warehouse=args.warehouse,
        priority_level=args.priority_level,
        risk_level=args.risk_level,
        confidence_level=args.confidence_level,
        limit=args.limit,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["artículo", "almacén", "acción recomendada", "cantidad sugerida", "prioridad", "confianza", "riesgo", "motivo", "siguiente acción"]
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_row(row) for row in rows)
    print({"registros_exportados": len(rows), "archivo": str(output_path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
