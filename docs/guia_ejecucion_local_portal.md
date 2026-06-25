# Guía de ejecución local

## 1. Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verificación:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 2. Frontend

En otra terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Abrir `http://127.0.0.1:5173`.

Por restricciones de lectura de dependencias dentro de OneDrive, el comando
`npm run dev` genera primero el build y luego ejecuta Vite Preview. El portal es
funcional en la misma URL; para reflejar cambios de código se reinicia el
comando.

## 3. CORS

FastAPI permite solicitudes GET desde:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

## 4. Diagnóstico

Si el portal muestra error:

1. Confirmar que `/health` responde.
2. Revisar `VITE_API_BASE_URL`.
3. Confirmar que frontend y backend usan los puertos 5173 y 8000.
4. Probar `/replenishment/summary` directamente.

## 5. Compilación

```powershell
cd frontend
npm run build
```

La salida queda en `frontend/dist/`, excluida de Git.
