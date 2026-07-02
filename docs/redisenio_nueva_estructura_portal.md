# Rediseño R1 - Nueva estructura funcional del portal

## Objetivo

La nueva experiencia convierte el dashboard tecnico en un portal de diagnostico logistico. La navegacion se reduce a cuatro modulos principales para responder preguntas de negocio de manera directa y en español.

## Navegacion principal

### Inicio

Modulo gerencial de entrada. Debe responder: "Que debe hacer hoy?"

Contenido previsto:

- Resumen ejecutivo de acciones.
- Abastecer ahora.
- Revisar antes de abastecer.
- Atender riesgo critico.
- No comprar.
- Plan recomendado para el horizonte operativo.
- Origen general del diagnostico SAP con lenguaje amigable.

Fuentes actuales:

- `GET /health`
- `GET /replenishment/summary`

Reglas de lenguaje:

- No mostrar nombres de tablas SAP.
- No mostrar WAPE, MAE ni segmentacion tecnica como indicadores principales.
- Evitar "Forecast"; usar "Salidas proyectadas" o "Proyeccion de consumo".

### Recomendaciones

Modulo operativo para priorizar articulos y acciones.

Contenido previsto:

- Lista de articulos con accion sugerida.
- Acciones: Abastecer, Revisar, No comprar, Atender critico y Monitorear.
- Cantidad sugerida, stock disponible, ingresos esperados, salidas comprometidas y consumo proyectado.
- Panel plegable de filtros avanzados.
- Apertura de detalle por articulo sin cambiar calculos.

Fuentes actuales:

- `GET /replenishment/suggestions`
- `GET /replenishment/item/{item_code}`

### Diagnostico por articulo

Modulo de consulta detallada para un articulo especifico.

Contenido previsto:

- Selector o busqueda de articulo.
- Stock disponible.
- Ingresos esperados.
- Salidas comprometidas.
- Consumo proyectado.
- Cantidad sugerida.
- Confianza expresada en lenguaje funcional.
- Documentos SAP relacionados, preparados para fases siguientes mediante desplegables.

Fuentes actuales:

- `GET /replenishment/suggestions`
- `GET /replenishment/item/{item_code}`

Limitacion R1:

- Los documentos SAP relacionados quedan como estructura visual hasta incorporar partidas abiertas reales.

### Analisis avanzado

Modulo tecnico controlado para usuarios logisticos o analistas.

Contenido previsto:

- Proyeccion de consumo.
- Inventario por almacen.
- Segmentacion tecnica.
- Calidad de datos.
- Detalle historico.
- Explicaciones sencillas junto a terminos tecnicos.

Fuentes actuales:

- `GET /forecast/summary`
- `GET /inventory/current`
- `GET /analytics/summary`

## Rutas nuevas

- `/`: redirige a `/inicio`.
- `/inicio`: modulo Inicio.
- `/recomendaciones`: modulo Recomendaciones.
- `/diagnostico-articulo`: modulo Diagnostico por articulo.
- `/analisis-avanzado`: modulo Analisis avanzado.

## Compatibilidad temporal

Las rutas antiguas se conservan como redirecciones:

- `/dashboard` -> `/inicio`
- `/replenishment` -> `/recomendaciones`
- `/critical` -> `/recomendaciones`
- `/overstock` -> `/recomendaciones`
- `/forecast` -> `/analisis-avanzado`
- `/abc-xyz` -> `/analisis-avanzado`
- `/inventory` -> `/analisis-avanzado`
- `/interpretation` -> `/inicio`

## Principios visuales

- Paleta sobria.
- Azul para informacion general.
- Verde para abastecer.
- Ambar para revisar.
- Rojo para riesgo critico.
- Gris para no comprar o sin accion.
- Sin exceso de colores por KPI.
- Sin tecnicismos dominantes en vistas gerenciales.

## Preparacion para fases siguientes

La estructura queda lista para incorporar:

- Calculo basado en movimientos de inventario.
- Partidas abiertas de SAP: ordenes de compra, venta y fabricacion.
- Trazabilidad por documento SAP.
- Analisis por almacen y horizonte operativo.
- Validacion gerencial de recomendaciones antes de cualquier automatizacion.
