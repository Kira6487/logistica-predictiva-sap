# Portal React local

Frontend de demostración para el Portal de Logística Predictiva integrado a SAP
Business One.

## Requisitos

- Node.js 20 o superior.
- Backend FastAPI ejecutándose en la URL indicada por `VITE_API_URL`.

## Configuración

```powershell
cd frontend
Copy-Item .env.example .env.local
```

Para desarrollo local:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Instalación y ejecución

```powershell
cd frontend
npm install
npm run dev
```

También puede utilizarse pnpm si se conserva el lockfile existente:

```powershell
pnpm install
pnpm run dev
```

Vite muestra la URL local (normalmente `http://127.0.0.1:5173`) al iniciar.

Rutas principales de la navegación R1:

- `/inicio`
- `/recomendaciones`
- `/diagnostico-articulo`
- `/analisis-avanzado`

`npm run dev` inicia Vite en modo desarrollo con recarga automática.

## Compilación

```powershell
npm run build
```

La compilación ejecuta primero la validación TypeScript y luego genera
`frontend/dist/`.

Para Vercel, seleccione `frontend/` como raíz del proyecto. El archivo
`vercel.json` conserva las rutas SPA y el build usa `VITE_API_URL`; no coloque
credenciales de base de datos en variables `VITE_`.

`VITE_API_URL` es obligatoria: el build falla con un mensaje explícito si no
está definida.

## Pantallas

- Inicio: resumen ejecutivo y acciones del día.
- Recomendaciones: acciones para abastecer, revisar, monitorear o no comprar.
- Diagnóstico por artículo: lectura detallada de stock, ingresos esperados,
  salidas comprometidas, consumo proyectado y cantidad sugerida.
- Análisis avanzado: proyección de consumo, inventario por almacén,
  segmentación técnica, calidad de datos y detalle histórico.

Las rutas anteriores se conservan temporalmente como redirecciones:

- `/dashboard` -> `/inicio`
- `/replenishment`, `/critical`, `/overstock` -> `/recomendaciones`
- `/forecast`, `/abc-xyz`, `/inventory` -> `/analisis-avanzado`
- `/interpretation` -> `/inicio`

El portal es informativo: no crea documentos, no modifica SAP y no automatiza
órdenes de compra.
