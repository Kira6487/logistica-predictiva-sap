import argparse
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.eda_service import build_analytics  # noqa: E402


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use formato YYYY-MM-DD.") from exc


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Ejecuta clasificaciones ABC, XYZ y ABC/XYZ."
    )
    value.add_argument("--date-from", type=parse_date)
    value.add_argument("--date-to", type=parse_date)
    value.add_argument("--item-code")
    value.add_argument("--item-group")
    value.add_argument("--warehouse-code")
    value.add_argument("--min-months", type=int, default=12)
    return value


def main() -> int:
    args = parser().parse_args()
    result = build_analytics(
        date_from=args.date_from,
        date_to=args.date_to,
        item_code=args.item_code,
        item_group=args.item_group,
        warehouse_code=args.warehouse_code,
        min_months=args.min_months,
    )
    export_dir = Path(__file__).resolve().parents[1] / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "ABC cantidad": export_dir / "abc_quantity_classification.csv",
        "ABC importe": export_dir / "abc_amount_classification.csv",
        "XYZ": export_dir / "xyz_classification.csv",
        "ABC/XYZ": export_dir / "abc_xyz_classification.csv",
    }
    result.abc_quantity.to_csv(
        paths["ABC cantidad"],
        index=False,
        encoding="utf-8-sig",
    )
    result.abc_amount.to_csv(
        paths["ABC importe"],
        index=False,
        encoding="utf-8-sig",
    )
    result.xyz.to_csv(paths["XYZ"], index=False, encoding="utf-8-sig")
    result.combined.to_csv(paths["ABC/XYZ"], index=False, encoding="utf-8-sig")

    print(f"Artículos clasificados: {len(result.combined):,}")
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
