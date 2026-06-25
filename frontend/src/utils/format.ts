export const numberFormat = new Intl.NumberFormat("es-PE", {
  maximumFractionDigits: 1,
});

export function formatNumber(value?: number | null) {
  return value === null || value === undefined ? "—" : numberFormat.format(value);
}

export function formatPercent(value?: number | null) {
  return value === null || value === undefined
    ? "—"
    : `${numberFormat.format(value)}%`;
}

export function formatCoverage(value?: number | null) {
  return value === null || value === undefined
    ? "Sin demanda"
    : `${numberFormat.format(value)} días`;
}
