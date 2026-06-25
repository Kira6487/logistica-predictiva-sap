# Contrato API del portal

## Configuración

Variable:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Endpoints consumidos

| Pantalla | Endpoints |
|---|---|
| Dashboard | `/health`, `/analytics/summary`, `/forecast/summary`, `/replenishment/summary` |
| Reposición | `/replenishment/suggestions`, `/replenishment/item/{item_code}` |
| Críticos | `/replenishment/critical` |
| Sobrestock | `/replenishment/overstock` |
| Forecast | `/forecast/summary`, `/forecast/candidates`, `/forecast/item/{item_code}` |
| ABC/XYZ | `/analytics/summary`, `/analytics/abc`, `/analytics/xyz`, `/analytics/abc-xyz` |
| Inventario | `/inventory/current?only_with_stock=true` |

## Ajustes de API

- Se agregó CORS limitado a los dos orígenes locales del portal.
- `/forecast/candidates` conserva sus campos y añade mejor modelo, WAPE, MAE y
  confianza mediante una unión con los resultados existentes.
- No se duplicó lógica en endpoints de dashboard.

## Convenciones

- Números ausentes se muestran como guion.
- Cobertura nula significa que no existe demanda proyectada positiva.
- `LOW` implica recomendación referencial.
- `NOT_RECOMMENDED` y `EXCLUDED` no generan compras.
- Las respuestas se consumen exclusivamente mediante GET.
