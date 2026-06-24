from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.replenishment_service import build_replenishment  # noqa: E402


def main() -> int:
    result = build_replenishment()
    export_dir = Path(__file__).resolve().parents[1] / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    sample = result.suggestions.head(100)
    sample.to_csv(
        export_dir / "replenishment_item_detail_sample.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"Muestra dashboard: {len(sample):,} filas")
    print(export_dir / "replenishment_item_detail_sample.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
