# Calidad de datos para forecasting

## Estados

| Estado | Interpretación |
|---|---|
| `OK` | Historia suficiente, demanda positiva y sin alertas principales |
| `INSUFFICIENT_HISTORY` | Menos de 12 meses con cantidad positiva |
| `INTERMITTENT_DEMAND` | Menos del 50% de los meses disponibles presentan venta |
| `NEGATIVE_DEMAND` | Cantidad neta acumulada negativa |
| `AMOUNT_ANOMALY` | Signos o importes mensuales inconsistentes |
| `ZERO_OR_NULL_VALUES` | Periodos observados con cantidad neta cero o importe cero relevante |
| `REVIEW_REQUIRED` | Métricas no interpretables o clasificación no disponible |

Las banderas se conservan aunque un estado de mayor prioridad determine el
estado principal. Por ejemplo, un artículo puede tener historia insuficiente y
también anomalía monetaria.

## Hallazgos

Estados principales observados:

| Estado | Artículos |
|---|---:|
| `INSUFFICIENT_HISTORY` | 4,243 |
| `ZERO_OR_NULL_VALUES` | 825 |
| `INTERMITTENT_DEMAND` | 149 |
| `NEGATIVE_DEMAND` | 19 |
| `AMOUNT_ANOMALY` | 12 |
| `OK` | 12 |

Las banderas agregadas detectan 1,068 artículos con alguna anomalía monetaria,
aunque muchos aparecen bajo otro estado principal de mayor prioridad.

## Candidatos a forecast

Se consideran candidatos preliminares 173 artículos. Esto no significa que
todos deban usar el mismo modelo:

- demanda estable o variable con historia: baseline y modelos estadísticos;
- demanda irregular: baseline robusto y validación temporal;
- demanda intermitente: Croston, SBA, TSB o reglas equivalentes;
- historia insuficiente: no entrenar todavía;
- demanda negativa o clasificación no disponible: revisar y excluir.

## Controles para Fase 3

1. Usar cantidad neta como objetivo.
2. Separar entrenamiento y backtesting temporal.
3. No imputar demanda positiva en meses sin venta.
4. Mantener una bandera para los 19 artículos con demanda negativa.
5. Evaluar los artículos por almacén cuando la decisión de reposición lo exija.
6. No usar el ABC por importe como verdad financiera hasta conciliar anomalías.
