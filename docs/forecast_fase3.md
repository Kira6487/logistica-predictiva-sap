# Forecast de demanda - Fase 3

## Objetivo

La Fase 3 compara modelos explicables por artículo, selecciona el de menor error
y genera demanda futura mensual. SAP continúa en modo de solo lectura.

## Universo

- Candidatos recibidos de Fase 2: 173.
- Artículos excluidos: 5,087.
- Motivos principales: 4,839 con historial insuficiente, 229 con valores cero o
  anomalías prioritarias y 19 con demanda negativa.
- Rango histórico: mayo de 2019 a diciembre de 2025.

Los meses sin venta se mantienen como demanda cero. No se eliminan ni se
interpolan, pues representan información relevante para series intermitentes.

## Partición temporal

Los últimos seis meses se reservan como test. Los modelos se entrenan solo con
periodos anteriores y no se utiliza partición aleatoria. Para series cortas, la
implementación admite un test de tres meses.

## Resultado

- Artículos modelados: 173.
- Comparaciones artículo-modelo: 1,533.
- Horizonte generado: enero a marzo de 2026.
- Registros futuros: 519.
- Confianza media: 18 artículos.
- Confianza baja: 155 artículos.
- Confianza alta: 0 artículos.

Métricas promedio de los modelos ganadores:

- WAPE: 104.41%.
- MAE: 4.93 unidades.
- RMSE: 6.98 unidades.
- Bias: -2.20 unidades.

El error relativo alto se explica por series de bajo volumen, ceros frecuentes
y demanda irregular. MAE y Bias deben leerse junto con WAPE; un error de pocas
unidades puede producir WAPE elevado cuando la demanda real del test es baja.

## Interpretación operativa

El forecast es técnicamente reproducible y trazable, pero todavía no debe
generar compras automáticas. Los 18 artículos con confianza media constituyen
el grupo inicial para una prueba controlada. Los restantes requieren reglas de
seguridad, revisión humana o métodos específicos para demanda intermitente.

## Ejecución

```powershell
python scripts\run_forecast_baseline.py
python scripts\run_forecast_model_comparison.py
```
