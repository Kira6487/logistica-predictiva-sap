# Arquitectura inicial

## Flujo de la Fase 1

```text
Azure SQL demo
Base erp_portfolio_demo (datos sintéticos)
        |
        | consultas SELECT de solo lectura
        v
Backend Python / FastAPI
        |
        | JSON y exportaciones CSV locales
        v
Portal web React (fase posterior)
```

SAP Business One continúa siendo el sistema transaccional. El backend consulta
la base existente sin insertar, actualizar o eliminar registros. En esta fase,
la API valida la conexión, perfila las tablas principales y calcula demanda
mensual neta.

## Componentes

- `app/core`: configuración de entorno y conexión SQLAlchemy/pyodbc.
- `app/services`: proveedor demo, consultas compatibles con el subconjunto SAP y
  lógica de extracción reutilizable.
- `app/api/routes`: endpoints HTTP.
- `app/schemas`: contratos de respuesta.
- `scripts`: diagnóstico y exportación para trabajo técnico.
- `tests`: pruebas aisladas que no dependen de SAP.

## Decisiones de seguridad

- La contraseña se lee desde `DB_PASSWORD` y nunca tiene valor por defecto.
- `.env.local` está excluido de Git.
- La API no devuelve usuario, contraseña ni cadena de conexión.
- Se recomienda reemplazar cuentas administrativas por un usuario SQL de solo
  lectura.
- Todas las consultas implementadas son `SELECT`.

## Evolución prevista

El proveedor de demostración es sintético y de solo lectura. La integración
productiva con SAP Business One debe implementarse como proveedor separado; no
se mezclan sus credenciales ni su esquema con `DATA_PROVIDER=demo`.
