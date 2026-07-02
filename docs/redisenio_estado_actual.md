# Rediseño R1 - Estado actual del portal

## Alcance auditado

Esta auditoria revisa el estado funcional actual del Portal de Logistica Predictiva para SAP Business One antes del rediseño de navegacion. El backend se mantiene como API de lectura y no se modifica el motor de calculo en esta fase.

## Estructura backend

- `backend/app/main.py`: registra FastAPI, CORS local y routers de lectura.
- `backend/app/api/routes/health.py`: endpoint de salud.
- `backend/app/api/routes/replenishment.py`: resumen, sugerencias, criticos, sobrestock y detalle por articulo.
- `backend/app/api/routes/forecast.py`: proyeccion, candidatos, modelos, resultados y detalle temporal.
- `backend/app/api/routes/inventory.py`: inventario actual por articulo y almacen.
- `backend/app/api/routes/analytics.py`: calidad de datos y segmentacion tecnica.
- `backend/app/api/routes/demand.py`: consumo historico mensual.
- `backend/app/api/routes/sap_diagnostics.py`: diagnostico de conexion SAP.
- `backend/app/services/`: servicios de consulta, calculo y carga de artefactos.
- `backend/tests/`: pruebas unitarias y de servicios existentes.

## Estructura frontend

- `frontend/src/App.tsx`: define rutas actuales de React Router.
- `frontend/src/layouts/PortalLayout.tsx`: layout principal con menu lateral y cabecera.
- `frontend/src/pages/`: paginas actuales del portal.
- `frontend/src/components/`: componentes reutilizables para tablas, estados, tarjetas y badges.
- `frontend/src/api/`: clientes HTTP por dominio funcional.
- `frontend/src/types/`: contratos TypeScript usados por las paginas.
- `frontend/src/styles.css`: estilos globales, paleta visual, layout, tablas, badges y paneles.

## Paginas actuales del frontend

- `DashboardPage`: tablero ejecutivo tecnico con KPIs, graficos de estados, prioridades, tipo de compra y confianza.
- `ReplenishmentPage`: tabla de reposicion sugerida con filtros por estado, recomendacion, prioridad, confianza y compras.
- `CriticalItemsPage`: lista de articulos criticos.
- `OverstockPage`: articulos con posible exceso de stock.
- `ForecastPage`: proyeccion por producto, metricas tecnicas y comparacion visual.
- `AbcXyzPage`: segmentacion tecnica.
- `InventoryPage`: inventario por almacen.
- `InterpretationPage`: explicacion de conceptos del modelo actual.

## Endpoints consumidos por el frontend

- `GET /health`: estado de API.
- `GET /replenishment/summary`: resumen de recomendaciones.
- `GET /replenishment/suggestions`: detalle de recomendaciones por articulo.
- `GET /replenishment/critical`: articulos criticos.
- `GET /replenishment/overstock`: articulos con posible exceso.
- `GET /replenishment/item/{item_code}`: detalle de reposicion y proyeccion por articulo.
- `GET /forecast/summary`: resumen de proyecciones.
- `GET /forecast/candidates`: articulos modelados.
- `GET /forecast/results`: resultados futuros.
- `GET /forecast/item/{item_code}`: historico, prueba y proyeccion futura de un articulo.
- `GET /inventory/current`: inventario actual.
- `GET /analytics/summary`: resumen analitico.
- `GET /analytics/abc-xyz`: segmentacion combinada.
- `GET /analytics/data-quality`: calidad de datos.

## Componentes reutilizables actuales

- `DataTable`: tabla paginada reutilizable.
- `KpiCard`: tarjeta de indicador.
- `LoadingState`, `ErrorState`, `EmptyState`: estados comunes.
- `StatusBadge`, `PriorityBadge`, `ConfidenceBadge`: etiquetas de estado operativo, prioridad y confianza.
- `ProductDetailDrawer`: detalle lateral por articulo.

## Que se conservara

- Backend FastAPI y endpoints actuales de lectura.
- Contratos de datos de reposicion, inventario, proyeccion y analitica.
- Componentes de tabla, estados de carga/error/vacio y drawer de detalle.
- Paginas antiguas como compatibilidad temporal, accesibles mediante redirecciones a los nuevos modulos.
- Reglas de solo lectura sobre SAP Business One.

## Que se fusionara

- `DashboardPage`, `InterpretationPage` y resumen operativo se fusionan conceptualmente en `Inicio`.
- `ReplenishmentPage`, `CriticalItemsPage` y `OverstockPage` se fusionan funcionalmente en `Recomendaciones`.
- `ForecastPage`, `InventoryPage` y `AbcXyzPage` se agrupan bajo `Analisis avanzado`.

## Que se reemplazara

- Menu lateral de 8 pestañas por 4 modulos: Inicio, Recomendaciones, Diagnostico por articulo y Analisis avanzado.
- Etiquetas gerenciales tecnicas por lenguaje funcional: "Forecast" pasa a "Salidas proyectadas" o "Proyeccion de consumo"; "Compra activa" pasa a "Abastecer ahora"; "Sobrestock" pasa a "No comprar" o "Exceso de stock".
- Vista inicial tecnica por resumen ejecutivo orientado a decision.

## Riesgos de cambiar la logica actual

- Alterar calculos de reposicion podria romper comparabilidad con la demo validada.
- Cambiar endpoints podria afectar paginas existentes y pruebas.
- Renombrar campos tecnicos en backend podria romper contratos TypeScript.
- Ocultar demasiada informacion tecnica podria limitar el analisis logistico avanzado.
- Reinterpretar metricas de confianza sin validar negocio podria inducir decisiones de compra no aprobadas.

## Recomendacion de orden de implementacion

1. Mantener backend sin cambios y conservar endpoints actuales.
2. Crear paginas base de la nueva navegacion.
3. Reducir menu lateral y configurar redirecciones desde rutas antiguas.
4. Mapear terminos tecnicos a lenguaje de usuario en frontend.
5. Preparar componentes gerenciales reutilizables.
6. Validar compilacion frontend y pruebas backend.
7. En una fase posterior, refactorizar calculo con movimientos de inventario y partidas abiertas de SAP.

## Validaciones iniciales

- `pytest`: no se pudo ejecutar porque `pytest` no esta disponible en el PATH de la sesion.
- `npm run build`: no se pudo ejecutar porque `npm` no esta disponible en el PATH de la sesion.
- No se detectaron cambios pendientes antes de iniciar la rama de trabajo.
