# Glosario funcional para usuarios

Este glosario define como traducir terminos tecnicos del proyecto a lenguaje claro para usuarios gerenciales y logisticos. Los terminos tecnicos pueden mantenerse en backend, documentacion tecnica o Analisis avanzado, pero no deben dominar las vistas principales.

## Mapeo principal

| Termino tecnico | Termino amigable recomendado | Uso sugerido |
| --- | --- | --- |
| Forecast | Salidas proyectadas / Proyeccion de consumo | Usar en Inicio, Recomendaciones y Diagnostico |
| Compra activa | Abastecer ahora | Accion principal de compra |
| Compra referencial | Revisar antes de abastecer | Accion que requiere criterio humano |
| Posible sobrestock | No comprar / Exceso de stock | Evitar compra o revisar capital inmovilizado |
| Confianza baja | Prediccion con cautela | Advertencia funcional |
| Confianza media | Prediccion usable | Señal de apoyo a decision |
| Comprometido | Salidas comprometidas | Inventario reservado o demandado |
| Pedido | Ingresos esperados | Cantidades por recibir |
| OINM | Movimientos de inventario registrados en SAP | Solo documentacion tecnica o explicacion avanzada |
| Ordenes de compra abiertas | Ingresos esperados | Partidas que aumentan disponibilidad futura |
| Ordenes de venta abiertas | Salidas comprometidas | Partidas que reducen disponibilidad futura |
| Ordenes de fabricacion | Produccion pendiente o consumo de componentes | Explicacion por contexto |
| ABC/XYZ | Segmentacion tecnica | Solo Analisis avanzado con explicacion |
| WAPE | Error porcentual de la proyeccion | Solo Analisis avanzado |
| MAE | Diferencia promedio de la proyeccion | Solo Analisis avanzado |
| Stock fisico | Inventario fisico | Conteo en almacen |
| Stock disponible | Stock disponible | Cantidad usable luego de compromisos |
| Safety stock | Stock de seguridad | Reserva minima recomendada |
| Item code | Codigo de articulo | Etiqueta visible aceptable |
| Warehouse | Almacen | Etiqueta visible en español |

## Reglas para vistas gerenciales

- No mostrar nombres de tablas SQL o SAP como etiquetas principales.
- No usar "Forecast" como titulo principal.
- No mostrar WAPE o MAE en Inicio.
- No mostrar ABC/XYZ en Inicio ni Recomendaciones.
- Priorizar acciones: Abastecer ahora, Revisar antes de abastecer, Atender riesgo critico, No comprar y Monitorear.
- Cuando se muestre un termino tecnico en Analisis avanzado, acompañarlo con una explicacion sencilla.

## Ejemplos de textos recomendados

- "Diagnostico logistico basado en consumo historico, salidas proyectadas y partidas abiertas de SAP Business One."
- "Consumo historico registrado en SAP."
- "Ordenes de compra abiertas."
- "Ordenes de venta abiertas."
- "Ordenes de fabricacion abiertas."
- "Inventario actual por almacen."
- "Prediccion con cautela: use la cantidad como referencia y valide antes de abastecer."

## Terminos que deben evitarse como etiquetas principales

- OINM
- OINV
- ORIN
- OITW
- OPOR
- ORDR
- OWOR
- Forecast
- WAPE
- MAE
- ABC/XYZ
