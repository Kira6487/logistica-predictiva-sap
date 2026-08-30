# Portal de Logística Predictiva para SAP Business One

Portal de demostración conectado en modo lectura a Azure SQL
`erp_portfolio_demo`. Todos los datos de esa base son sintéticos.

## Alcance actual

- API FastAPI con health check.
- Diagnóstico de conexión y tablas SAP.
- Extracción de demanda mensual neta (facturas menos notas de crédito).
- Exportación local a CSV para análisis exploratorio.

Incluye backend analítico, forecasting, reposición y un portal React local de
demostración. El add-on SAP y el despliegue productivo continúan fuera del
alcance actual.

La fase R1 prepara una navegación funcional más simple para usuarios
gerenciales y logísticos: Inicio, Recomendaciones, Diagnóstico por artículo y
Análisis avanzado. No cambia el motor principal de cálculo ni escribe
información en SAP.

## Inicio rápido

Consulta [backend/README.md](backend/README.md) para configurar el entorno,
ejecutar la API y correr los scripts de diagnóstico y extracción.

Consulta [frontend/README.md](frontend/README.md) para levantar el portal local.

La documentación del rediseño funcional está en:

- [docs/redisenio_estado_actual.md](docs/redisenio_estado_actual.md)
- [docs/redisenio_nueva_estructura_portal.md](docs/redisenio_nueva_estructura_portal.md)
- [docs/glosario_funcional_usuario.md](docs/glosario_funcional_usuario.md)

## Arquitectura

La solución mantiene acceso de solo lectura:

`Azure SQL demo / adaptador SAP B1 -> FastAPI -> React en Vercel`

El proveedor `demo` está separado del adaptador para una futura integración
productiva con SAP Business One. Más detalle en
[docs/arquitectura_inicial.md](docs/arquitectura_inicial.md).

## Configuración, pruebas y despliegue

1. Configure `DB_PASSWORD` localmente; nunca la escriba en el chat, código o Git.
2. Siga [backend/README.md](backend/README.md) para API, diagnóstico y pruebas.
3. Siga [frontend/README.md](frontend/README.md) para el portal local.
4. Consulte [DEPLOYMENT.md](DEPLOYMENT.md) para App Service/Container Apps y el
   firewall restringido.
