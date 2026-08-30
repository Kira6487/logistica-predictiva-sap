# Validación de Fase 1 con datos reales

## Resultado

- Fecha: 24 de junio de 2026.
- La validación debe ejecutarse contra el servidor definido en `.env.local`.
- Base demo: `erp_portfolio_demo` (datos sintéticos).
- SQL Server: 15.0.2000.5, Developer Edition de 64 bits.
- Modo: solo lectura.
- Decisión: apto para continuar a Fase 2 ABC/XYZ.

## Conectividad y API

La configuración permite omitir `DB_PORT`; la conexión por nombre de servidor
funcionó sin forzar `localhost:1433`.

- `GET /health`: HTTP 200.
- `GET /sap/diagnostics/connection`: HTTP 200.
- `GET /demand/monthly`: HTTP 200, 6,792 filas para los últimos 24 meses.
- `pytest`: 2 pruebas aprobadas, 0 fallidas.

## Objetos SAP encontrados

Se encontraron todas las tablas principales y opcionales solicitadas:

`OINV`, `INV1`, `ORIN`, `RIN1`, `OITM`, `OITW`, `OWHS`, `OCRD`, `OSLP`,
`OITB`, `OBTN`, `OBTQ`, `IBT1`, `OPOR`, `POR1`, `OPDN`, `PDN1` y `OINM`.

`IBT1` y `OINM` son vistas. Las demás son tablas de usuario. Todas las columnas
críticas verificadas existen.

## Rango de fechas

- Facturas activas: 31 de mayo de 2019 a 23 de diciembre de 2025.
- Notas de crédito activas: 31 de mayo de 2019 a 23 de diciembre de 2025.
- Demanda con líneas de artículo: junio de 2019 a diciembre de 2025.
- Periodos con demanda: 78.

Mayo de 2019 contiene 391 líneas sin `ItemCode` y ninguna línea de artículo; por
eso el primer periodo analítico es junio. Abril de 2020 no contiene líneas
activas de artículo. La base no presenta documentos activos desde 2014; el
alcance real disponible comienza en 2019.

## Demanda neta de todo el histórico

- Artículos distintos: 5,260.
- Filas mensuales por artículo y almacén: 25,990.
- Cantidad neta: 182,628.5 unidades.
- Importe neto basado en `LineTotal`: 104,218,296.96.

| Año | Cantidad neta | Importe neto |
|---:|---:|---:|
| 2019 | 16,752.0 | 9,661,737.19 |
| 2020 | 22,397.0 | 9,784,735.43 |
| 2021 | 29,326.0 | 16,498,710.79 |
| 2022 | 28,950.5 | 19,387,479.67 |
| 2023 | 29,201.4 | 20,444,574.18 |
| 2024 | 30,844.6 | 17,270,423.08 |
| 2025 | 25,157.0 | 11,170,636.62 |

## Hallazgos de calidad

No se detectaron artículos de líneas que falten en `OITM`, fechas fuera de
2014-2025 ni meses con cantidad neta total negativa. Los documentos cancelados
se excluyen correctamente.

Hallazgos no bloqueantes:

- 791 líneas de factura y 235 de nota de crédito sin `ItemCode`; coinciden con
  líneas de cantidad cero y quedan fuera de la demanda por producto.
- 3,002 líneas de factura y 508 de nota de crédito tienen `LineTotal = 0`.
- 2,378 líneas de facturas canceladas y 180 de notas canceladas existen, pero
  son excluidas por la consulta.
- 287 artículos presentan más de una descripción histórica.
- 19 artículos tienen notas de crédito acumuladas mayores que sus facturas y
  demanda neta acumulada negativa.
- 3,373 artículos aparecen únicamente en uno o dos meses; requieren tratamiento
  especial como series nuevas, esporádicas o intermitentes.
- Marzo de 2025 tiene importe neto negativo de `-4,994,400.16`, aunque conserva
  cantidad neta positiva de 2,255 unidades.
- 270 facturas activas tienen `DocTotal = 0` pese a presentar `LineTotal`
  agregado distinto de cero; deben revisarse antes de usar importes como base
  financiera oficial.

## Moneda e importes

La muestra confirma que `LineTotal` está expresado en moneda local. Para
documentos USD, `TotalFrgn` representa el importe de línea en moneda extranjera.
Las diferencias entre la suma de líneas y `DocTotal` pueden incluir impuestos,
gastos, descuentos de cabecera y redondeos.

La cantidad neta es adecuada para ABC/XYZ de demanda. El importe neto basado en
`LineTotal` puede emplearse como aproximación analítica, pero los casos de
`DocTotal = 0` y el importe negativo de marzo de 2025 deben conciliarse antes de
usar el valor como indicador contable.

## Archivos generados

- `backend/exports/phase1_validation_report.txt`
- `backend/exports/phase1_yearly_summary.csv`
- `backend/exports/phase1_monthly_summary.csv`
- `backend/exports/phase1_data_issues.csv`
- `backend/exports/monthly_demand_20260624_153303.csv`

La carpeta `backend/exports/` permanece excluida de Git.

## Decisión

**Sí se puede continuar a Fase 2 ABC/XYZ.**

Condiciones recomendadas:

1. Construir ABC principalmente con cantidad neta y, si se usa valor, conservar
   una bandera de calidad para los importes anómalos.
2. Separar artículos con uno o dos meses activos antes de calcular XYZ.
3. Revisar los 19 artículos con demanda neta negativa.
4. Mantener el análisis por almacén mediante `WhsCode`.
