# Arquitectura inicial

## Flujo de la Fase 1

```text
SAP Business One
Base SQL Server SBO_MEDINET_MIGRACION
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
- `app/services`: consultas SAP y lógica de extracción reutilizable.
- `app/api/routes`: endpoints HTTP.
- `app/schemas`: contratos de respuesta.
- `scripts`: diagnóstico y exportación para trabajo técnico.
- `tests`: pruebas aisladas que no dependen de SAP.

## Decisiones de seguridad

- Las credenciales se leen desde `.env.local`.
- `.env.local` está excluido de Git.
- La API no devuelve usuario, contraseña ni cadena de conexión.
- Se recomienda reemplazar cuentas administrativas por un usuario SQL de solo
  lectura.
- Todas las consultas implementadas son `SELECT`.

## Evolución prevista

La base o esquema analítico separado, los procesos ETL, forecasting, reposición,
frontend React y add-on SAP se desarrollarán en fases posteriores. El add-on
solo servirá inicialmente como lanzador del portal local; esta fase no crea
documentos ni escribe datos en SAP.
