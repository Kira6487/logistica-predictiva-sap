# Análisis exploratorio de demanda - Fase 2

## Objetivo

La Fase 2 transforma la demanda mensual neta de SAP en métricas explicables por
artículo. No entrena modelos: determina qué series tienen suficiente historia,
qué tan estables son y cuáles necesitan tratamiento especial.

## Alcance analizado

- Base demo: `erp_portfolio_demo` (datos sintéticos).
- Rango: 31 de mayo de 2019 a 23 de diciembre de 2025.
- Meses calendario disponibles: 80.
- Artículos analizados: 5,260.
- Demanda: facturas activas menos notas de crédito activas.
- Nivel: artículo; el almacén puede filtrarse con `warehouse_code`.

Cuando no se filtra almacén, las cantidades de todos los almacenes se agregan
por artículo y periodo. Los meses sin transacciones se rellenan con cero para
que promedio, desviación y coeficiente de variación reflejen la discontinuidad
real de la demanda.

## Métricas

Para cada artículo se calculan:

- primer y último periodo con cantidad positiva;
- meses con y sin venta;
- cantidad e importe netos acumulados;
- promedio, desviación estándar y coeficiente de variación mensual;
- mínimo y máximo mensual;
- cantidades de los últimos 3, 6 y 12 meses;
- indicadores de demanda negativa, intermitencia y anomalía monetaria;
- estado de calidad de datos.

El coeficiente de variación se calcula como:

`desviación estándar mensual / promedio mensual`

La desviación y el promedio incluyen los meses con cero demanda.

## Resultado principal

| Indicador | Resultado |
|---|---:|
| Artículos con menos de 12 meses de venta | 4,839 |
| Artículos intermitentes con historia suficiente | 324 |
| Artículos con demanda acumulada negativa | 19 |
| Artículos con anomalía monetaria | 1,068 |
| Recomendados inicialmente para forecast | 173 |
| No recomendados todavía | 5,087 |

La elevada proporción de series cortas e intermitentes indica que un único
modelo para todo el catálogo sería poco confiable. La Fase 3 debe trabajar por
segmento y mantener baselines simples.

## Cantidad frente a importe

La cantidad neta es la base principal porque representa unidades demandadas y
no depende de moneda, impuestos o documentos con `DocTotal = 0`.

El importe neto se conserva como dimensión secundaria. Existen documentos y
meses con inconsistencias monetarias, por lo que sus clasificaciones incluyen
la advertencia `AMOUNT_REVIEW_REQUIRED`.

## Uso

```powershell
python scripts\run_eda_analysis.py
```

Genera `eda_item_metrics.csv`, `data_quality_report.csv` y
`analytics_summary.csv` dentro de `backend/exports/`.
