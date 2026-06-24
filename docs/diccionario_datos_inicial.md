# Diccionario de datos inicial

> Todas las consultas de esta fase son de solo lectura. No se modifican tablas
> ni documentos de SAP Business One.

## Tablas utilizadas directamente

| Tabla | Contenido | Uso inicial |
|---|---|---|
| `OINV` | Cabecera de facturas de clientes | Fecha del documento y estado de cancelación |
| `INV1` | Líneas de facturas de clientes | Artículo, cantidad y total de línea positivo |
| `ORIN` | Cabecera de notas de crédito de clientes | Fecha del documento y estado de cancelación |
| `RIN1` | Líneas de notas de crédito de clientes | Artículo, cantidad y total de línea a restar |
| `OITM` | Maestro de artículos | Nombre y grupo asociado al código de artículo |
| `OITB` | Grupos de artículos | Descripción de familia o grupo |

## Tablas verificadas para fases próximas

| Tabla | Contenido | Uso futuro previsto |
|---|---|---|
| `OITW` | Inventario por artículo y almacén | Stock, comprometido y pedido |
| `OWHS` | Maestro de almacenes | Nombre y atributos del almacén |
| `OCRD` | Socios de negocio | Clientes y proveedores |
| `OSLP` | Empleados de ventas | Segmentación comercial opcional |

## Dataset de demanda mensual

| Campo | Descripción |
|---|---|
| `year` | Año de `DocDate` |
| `month` | Mes numérico de `DocDate` |
| `period` | Periodo `YYYY-MM` |
| `item_code` | Código SAP del artículo |
| `item_name` | Descripción del artículo desde `OITM` |
| `warehouse_code` | Almacén de la línea desde `INV1.WhsCode` o `RIN1.WhsCode` |
| `net_quantity` | Cantidad facturada menos cantidad acreditada |
| `net_sales_total` | Total de líneas facturadas menos líneas acreditadas |
| `item_group` | Grupo del artículo desde `OITB` |

## Supuestos que deben validarse con datos reales

- `CANCELED = 'N'` identifica documentos vigentes en `OINV` y `ORIN`.
- Las cantidades de `RIN1` deben restarse completas. Notas de crédito de solo
  valor, líneas sin artículo o documentos basados parcialmente pueden requerir
  reglas adicionales.
- `LineTotal` representa importe neto de línea en moneda local antes de impuesto.
  Debe confirmarse el tratamiento de moneda extranjera, descuentos, gastos y
  redondeos.
- La agregación admite producto, mes y almacén mediante `WhsCode`. El endpoint
  conserva sus parámetros originales y agrega `warehouse_code` como filtro
  opcional.
- Si una instalación SAP tiene personalizaciones, campos eliminados o vistas en
  lugar de tablas estándar, el diagnóstico permitirá detectar el hallazgo antes
  de ajustar las consultas.
