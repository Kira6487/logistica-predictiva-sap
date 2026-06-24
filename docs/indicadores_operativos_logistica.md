# Indicadores operativos de logística

## Inventario

| Indicador | Resultado |
|---|---:|
| Stock físico | 22,660 |
| Stock comprometido | 170 |
| Stock en pedido | 4,444 |
| Stock disponible | 22,490 |

Los totales agregan los 21 almacenes. Unidades de medida diferentes pueden
coexistir entre artículos, por lo que estos totales sirven como control técnico
y no como indicador financiero.

## Estados

| Estado | Artículos |
|---|---:|
| Críticos o sin stock con demanda | 17 |
| Revisión de cobertura | 3 |
| Saludables | 21 |
| Sobrestock | 50 |
| Sin demanda futura | 82 |
| No recomendados | 5,087 |

## Recomendaciones

| Tipo | Artículos |
|---|---:|
| Compra sugerida | 12 |
| Compra referencial | 25 |
| Monitor | 4 |
| No comprar | 131 |
| Revisión manual directa | 1 |
| Excluidos | 5,087 |

Hay 171 artículos modelados con alguna condición de revisión manual, incluyendo
confianza baja, demanda irregular o anomalías. Esto no significa que todos
necesiten compra.

## Prioridad

| Nivel | Artículos |
|---|---:|
| Alta | 7 |
| Media | 10 |
| Baja | 5,243 |

La prioridad no reemplaza el criterio del comprador. Ordena la revisión y hace
visibles los productos con demanda proyectada, baja cobertura e importancia
ABC.

## Uso futuro en el portal

El portal podrá consumir:

- resumen ejecutivo;
- ranking de compras sugeridas;
- críticos sin stock;
- sobrestock;
- detalle por artículo;
- vista de exportación.

Cada fila incluye forecast, confianza, inventario, seguridad, cobertura,
clasificaciones, prioridad y explicación.
