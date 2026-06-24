# Reglas de reposición

## Inventario

- Stock disponible = `OnHand - IsCommited`.
- Stock proyectado = stock disponible + `OnOrder`.

## Cobertura

La demanda promedio diaria usa meses de 30 días:

`cobertura = stock disponible / demanda proyectada diaria`

Si la demanda es cero, la cobertura no aplica. Si hay demanda y stock
disponible no positivo, la cobertura es cero.

## Stock de seguridad

Regla inicial configurable:

- confianza media: 20%;
- confianza baja: 35%;
- intermitente: 40%;
- clase A: 10% adicional;
- clase B: 5% adicional;
- clase C: sin adicional.

Para compatibilidad futura, confianza alta utiliza 15%. El porcentaje se aplica
a la demanda total del horizonte y nunca genera valores negativos.

## Compra

`demanda horizonte + seguridad - disponible - en pedido`

El valor se conserva sin redondear y la recomendación final se redondea hacia
arriba. Los resultados negativos se convierten en cero. Los artículos
excluidos nunca generan compra.

## Estado operativo

Prioridad de clasificación:

1. `NOT_RECOMMENDED`
2. `NO_STOCK_WITH_DEMAND`
3. `CRITICAL`, cobertura menor a 30 días
4. `REVIEW`, cobertura de 30 a menos de 60 días
5. `OVERSTOCK`, cobertura mayor a 180 días
6. `NO_DEMAND`
7. `HEALTHY`

El intervalo de 60 a 180 días se conserva como `HEALTHY`; el portal puede
mostrar una advertencia visual adicional entre 120 y 180 días.

## Tipo de recomendación

- `PURCHASE_SUGGESTED`: cantidad positiva y confianza media/alta.
- `REFERENTIAL_PURCHASE`: cantidad positiva y confianza baja.
- `MONITOR`: sin compra inmediata.
- `NO_PURCHASE`: sobrestock o sin demanda.
- `MANUAL_REVIEW`: condición crítica sin recomendación cuantitativa confiable.
- `EXCLUDED`: fuera del universo apto.

## Prioridad

El puntaje suma criticidad, clase ABC, confianza, baja cobertura y magnitud de
compra; resta 30 puntos cuando existen alertas que requieren revisión. Se limita
entre 0 y 100:

- alta: 70 o más;
- media: 40 a 69;
- baja: menos de 40.
