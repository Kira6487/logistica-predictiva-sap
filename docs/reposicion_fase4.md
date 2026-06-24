# Reposición sugerida - Fase 4

## Objetivo

La Fase 4 cruza forecast, inventario SAP y segmentación ABC/XYZ para producir
recomendaciones operativas explicables. No crea órdenes de compra ni modifica
SAP.

## Fuentes

- Forecast enero-marzo de 2026.
- Inventario por almacén desde `OITW`.
- Artículos y grupos desde `OITM` y `OITB`.
- Almacenes desde `OWHS`.
- Clasificaciones y calidad de Fase 2.

Sin filtro de almacén, stock y forecast se agregan a nivel empresa (`ALL`). Con
`warehouse_code`, el análisis se recalcula únicamente para ese almacén.

## Resultado real

| Indicador | Resultado |
|---|---:|
| Artículos de inventario | 8,007 |
| Almacenes | 21 |
| Artículos analizados para reposición | 5,260 |
| Compras sugeridas o referenciales | 37 |
| Compras activas, confianza media | 12 |
| Compras referenciales, confianza baja | 25 |
| Cantidad sugerida total | 2,523 |
| Artículos críticos | 17 |
| Posible sobrestock | 50 |

Los 5,087 artículos excluidos del forecast permanecen visibles como
`NOT_RECOMMENDED/EXCLUDED`, pero su compra sugerida se fuerza a cero.

## Limitación monetaria

No se calcula valor total de compra porque aún no se ha validado una fuente de
costo unitario, lista de precios ni moneda de compra. La salida actual expresa
cantidades.

## Criterio de uso

Las 12 recomendaciones de confianza media pueden utilizarse en un piloto con
aprobación humana. Las 25 recomendaciones de confianza baja son únicamente
referenciales. Ninguna recomendación crea documentos SAP.
