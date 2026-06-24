# Clasificación ABC/XYZ

## ABC: importancia relativa

La clasificación ABC ordena los artículos de mayor a menor contribución:

- **A:** hasta 80% acumulado.
- **B:** de 80% a 95%.
- **C:** de 95% a 100%.

El criterio principal es `net_quantity_total`. Los artículos con cantidad neta
cero o negativa quedan `UNCLASSIFIED` y se revisan por separado.

Resultado por cantidad:

| Clase | Artículos |
|---|---:|
| A | 51 |
| B | 834 |
| C | 4,172 |
| Sin clasificación positiva | 203 |

Existe una clasificación secundaria por `net_amount_total`:

| Clase | Artículos |
|---|---:|
| A | 152 |
| B | 525 |
| C | 4,369 |
| Sin clasificación positiva | 214 |

La clasificación monetaria no sustituye a cantidad. 1,084 artículos presentan
`AMOUNT_REVIEW_REQUIRED` por anomalías o importes no positivos.

## XYZ: estabilidad

XYZ usa el coeficiente de variación mensual:

- **X:** CV menor o igual a 0.50.
- **Y:** CV mayor a 0.50 y menor o igual a 1.00.
- **Z:** CV mayor a 1.00.

Antes de aplicar esos umbrales:

- menos de 12 meses con venta: `INSUFFICIENT_HISTORY`;
- demanda intermitente: `INTERMITTENT`;
- demanda acumulada negativa: `REVIEW_REQUIRED`.

Resultado:

| Clase | Artículos |
|---|---:|
| X | 1 |
| Y | 27 |
| Z | 50 |
| Intermitente | 324 |
| Historial insuficiente | 4,839 |
| Revisión requerida | 19 |

## Combinación ABC/XYZ

Las clases normales se expresan como `AX`, `BY` o `CZ`. Los estados especiales
se conservan, por ejemplo `A-INTERMITTENT` o
`C-INSUFFICIENT_HISTORY`.

Grupos principales:

| Grupo | Artículos |
|---|---:|
| C-INSUFFICIENT_HISTORY | 4,172 |
| B-INSUFFICIENT_HISTORY | 473 |
| B-INTERMITTENT | 302 |
| REVIEW_REQUIRED | 203 |
| BZ | 43 |
| A-INTERMITTENT | 22 |
| BY | 16 |
| AY | 11 |
| AZ | 7 |
| AX | 1 |

## Recomendación preliminar

- `AX` y `AY`: candidatos fuertes.
- `AZ`: forecast con cautela y revisión de estacionalidad.
- `BX` y `BY`: forecast estándar.
- `BZ`, `CX`, `CY` y `CZ`: baseline simple o promedio móvil.
- `*-INTERMITTENT`: método específico para demanda intermitente.
- `*-INSUFFICIENT_HISTORY`: acumular más historia.
- `REVIEW_REQUIRED`: excluir temporalmente.

```powershell
python scripts\run_abc_xyz_analysis.py
```
