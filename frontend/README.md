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
VITE_API_BASE_URL=http://127.0.0.1:8000
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

En esta carpeta sincronizada con OneDrive, `npm run dev` compila y sirve una
vista previa local estable. Si modifica el código, reinicie el comando para
recompilar.

## Compilación

```powershell
npm run build
```

La compilación ejecuta primero la validación TypeScript y luego genera
`frontend/dist/`.

## Pantallas

- Dashboard ejecutivo.
- Reposición sugerida.
- Productos críticos.
- Sobrestock.
- Forecast.
- ABC/XYZ.
- Inventario.
- Interpretación de indicadores.

El portal es informativo: no crea documentos, no modifica SAP y no automatiza
órdenes de compra.
