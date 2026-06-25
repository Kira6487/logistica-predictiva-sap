# Portal React - Fase 5

## Alcance

La primera versión local presenta los resultados de demanda, forecast,
inventario y reposición en una interfaz navegable orientada a gerencia,
logística, compras y almacén.

Tecnologías:

- React y TypeScript.
- Vite.
- React Router.
- Recharts.
- Lucide React.
- CSS propio, sin framework visual pesado.

## Navegación

El layout utiliza sidebar, header fijo y área central. Incluye:

1. Dashboard.
2. Reposición sugerida.
3. Productos críticos.
4. Sobrestock.
5. Forecast.
6. ABC/XYZ.
7. Inventario.
8. Interpretación.

## Dashboard

Muestra nueve KPIs y cuatro gráficos:

- distribución de estados operativos;
- prioridad;
- compra activa frente a referencial;
- confianza del forecast.

No se muestran valores monetarios porque costos y monedas de compra aún no han
sido validados.

## Tablas operativas

Las tablas incluyen paginación local, filtros, búsqueda y estados vacíos. El
detalle lateral de producto muestra inventario, cobertura, forecast,
clasificación, prioridad y motivo de recomendación.

## Experiencia y advertencias

La interfaz diferencia visualmente:

- compra sugerida activa;
- compra referencial;
- revisión manual;
- no compra;
- críticos y sobrestock.

Se mantienen visibles las advertencias:

- las compras de baja confianza son referenciales;
- no se automatizan órdenes de compra;
- los valores monetarios están pendientes.

## Limitaciones

- Sin autenticación ni roles.
- Sin escritura en SAP.
- Sin add-on.
- Sin exportación Excel desde el navegador.
- Inventario filtrado y paginado en memoria para la demo.
- Bundle inicial sin división por rutas; queda como mejora de rendimiento.
