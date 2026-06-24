from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.inventory_service import get_current_inventory  # noqa: E402
from app.services.replenishment_service import build_replenishment  # noqa: E402


def main() -> int:
    result = build_replenishment()
    export_dir = Path(__file__).resolve().parents[1] / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    inventory = get_current_inventory()
    inventory.to_csv(
        export_dir / "current_inventory_snapshot.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result.suggestions.to_csv(
        export_dir / "replenishment_suggestions.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result.suggestions[
        result.suggestions["stock_status"].isin(
            ["CRITICAL", "NO_STOCK_WITH_DEMAND"]
        )
    ].to_csv(
        export_dir / "replenishment_critical_items.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result.suggestions[
        result.suggestions["stock_status"] == "OVERSTOCK"
    ].to_csv(
        export_dir / "replenishment_overstock_items.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame([result.summary]).to_csv(
        export_dir / "replenishment_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"Inventario: {len(inventory):,} filas")
    print(f"Artículos evaluados: {len(result.suggestions):,}")
    print(
        "Compra sugerida/referencial: "
        f"{result.summary['items_with_purchase']:,} artículos"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
