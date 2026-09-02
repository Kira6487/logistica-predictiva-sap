# Arquitectura CSS del portal

`main.css` es el único punto de entrada de estilos de la aplicación operativa. Importa los módulos en este orden: tokens, base, layout, componentes, páginas y responsive.

## Dónde trabajar

- `base/`: reset, variables y jerarquía tipográfica global.
- `layout/`: shell, sidebar, contenido, topbar y breakpoints.
- `components/`: elementos reutilizables como tablas, formularios, filtros, botones, badges, cards, alertas y modales.
- `pages/`: estilos exclusivos de una vista; actualmente recomendaciones, validaciones y diagnóstico.
- `tokens.css`: colores, espaciado, radios, sombras, tipografía y medidas del layout.

Las tablas activas usan `ResizableTable` desde `operational/components.tsx`. Cada vista define sus columnas, tipo (`short`, `medium` o `long`) y límites; el componente gestiona resize, teclado, wrapping y persistencia local por `storageKey`.

## Reglas para nuevas vistas

1. No agregues estilos de página a `base/globals.css`.
2. No agregues estilos genéricos a `pages/*.css`.
3. Reutiliza tokens y componentes existentes.
4. Reutiliza `components/tables.css` y `ResizableTable` para tablas nuevas.
5. Evita `!important`; corrige la especificidad o la arquitectura.
6. Revisa los breakpoints existentes antes de crear un media query.
7. Aísla en `pages/*.css` solo lo que sea realmente exclusivo de una vista.
8. Los nuevos componentes compartidos deben tener estilos en `components/`.

La carpeta `src/pages` y `src/components/DataTable.tsx` contienen una implementación legacy no montada por el entry point actual; la aplicación activa vive en `src/operational`.
