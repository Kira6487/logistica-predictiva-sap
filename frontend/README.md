# Portal React local

Frontend de demostración para el Portal de Logística Predictiva integrado a SAP
Business One.

## Requisitos

- Node.js 20 o superior.
- Backend FastAPI ejecutándose en `http://127.0.0.1:8000`.

## Configuración

```powershell
cd frontend
Copy-Item .env.example .env.local
```

Valor predeterminado:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Instalación y ejecución

```powershell
cd frontend
npm install
npm run dev
```

También puede utilizarse pnpm:

```powershell
pnpm install
pnpm run dev
```

Portal: `http://127.0.0.1:5173`

Rutas principales de la navegación R1:

- `/inicio`
- `/recomendaciones`
- `/diagnostico-articulo`
- `/analisis-avanzado`

En esta carpeta sincronizada con OneDrive, `npm run dev` compila y sirve una
vista previa local estable. Si modifica el código, reinicie el comando para
recompilar.

## Compilación

```powershell
npm run build
```

La compilación ejecuta primero la validación TypeScript y luego genera
`frontend/dist/`.

Para Vercel, seleccione `frontend/` como raíz del proyecto. El archivo
`vercel.json` conserva las rutas SPA y el build usa `VITE_API_URL`; no coloque
credenciales de base de datos en variables `VITE_`.

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
