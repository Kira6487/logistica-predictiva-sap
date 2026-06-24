# Modelos de forecast utilizados

## Baselines

- `naive_last_value`: repite el último valor observado.
- `seasonal_naive_12`: usa el mismo mes del año anterior.
- `moving_average_3`: promedio de tres meses.
- `moving_average_6`: promedio de seis meses.
- `moving_average_12`: promedio de doce meses.

Los baselines son esenciales: un modelo más complejo solo aporta valor si los
supera en backtesting.

## Estadísticos

- `exponential_smoothing`: suavizamiento exponencial simple para el nivel.
- `holt_winters`: tendencia y estacionalidad aditivas de doce meses.

Holt-Winters requiere al menos 24 meses. Los errores de ajuste se registran por
artículo y no interrumpen el lote.

## Demanda intermitente

`croston` estima por separado tamaño de demanda e intervalo entre demandas. Solo
se evalúa en artículos clasificados como intermitentes. Si existen menos de dos
observaciones positivas, usa como fallback el promedio de demandas positivas.

## Machine learning

`random_forest_global` se entrena con observaciones de todos los candidatos:

- año, mes y número de periodo;
- rezagos 1, 2, 3 y 6;
- medias móviles 3 y 6;
- desviación móvil de 3 meses;
- clases ABC y XYZ codificadas.

La predicción de test y futuro es recursiva: los rezagos posteriores utilizan
predicciones previas, no valores reales futuros. Esto evita leakage.

Random Forest fue seleccionado como ganador para 4 artículos. Su rendimiento
medio no superó a los promedios móviles en este conjunto, por lo que permanece
como modelo complementario y no predeterminado.

## Frecuencia de modelos ganadores

| Modelo | Artículos |
|---|---:|
| moving_average_3 | 56 |
| seasonal_naive_12 | 26 |
| moving_average_12 | 25 |
| naive_last_value | 25 |
| exponential_smoothing | 15 |
| holt_winters | 11 |
| moving_average_6 | 8 |
| random_forest_global | 4 |
| croston | 3 |
