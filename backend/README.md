# Backend FastAPI

Backend inicial de solo lectura para SAP Business One sobre SQL Server.

## Requisitos

- Python 3.11 o superior.
- Azure SQL accesible desde el equipo.
- Microsoft ODBC Driver 18 for SQL Server.
- Usuario `portal_demo_reader` con permisos de lectura.

## 1. Crear y activar el entorno virtual

Desde la carpeta `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configurar variables

Copie `.env.example` como `.env.local` en la raíz del repositorio:

```powershell
Copy-Item ..\.env.example ..\.env.local
```

Defina `DB_PASSWORD` exclusivamente en el entorno local o en el administrador de
secretos del servicio. No confirme `.env.local` en Git ni imprima la contraseña.
La configuración usa `DB_ENCRYPT=yes` y `DB_TRUST_SERVER_CERTIFICATE=no`.

`DB_PORT` debe ser `1433` para Azure SQL.

## 4. Ejecutar la API

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Documentación interactiva: `http://127.0.0.1:8000/docs`

## 5. Probar endpoints

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/db
Invoke-RestMethod http://127.0.0.1:8000/sap/diagnostics/connection
Invoke-RestMethod http://127.0.0.1:8000/sap/diagnostics/schema
Invoke-RestMethod "http://127.0.0.1:8000/demand/monthly"
Invoke-RestMethod "http://127.0.0.1:8000/demand/monthly?date_from=2024-01-01&date_to=2025-12-31&item_code=ITEM001"
Invoke-RestMethod "http://127.0.0.1:8000/demand/monthly?warehouse_code=01"
```

Sin fechas, demanda usa los últimos 24 meses respecto de la máxima fecha activa
en `OINV`, no respecto del reloj del equipo.

## 6. Ejecutar diagnóstico SAP

```powershell
python scripts\diagnose_sap_db.py
```

El script comprueba la base, las tablas principales, sus conteos y el rango de
`OINV.DocDate`.

## 7. Exportar demanda mensual

Rango predeterminado:

```powershell
python scripts\extract_monthly_demand.py
```

Rango explícito:

```powershell
python scripts\extract_monthly_demand.py --date-from 2024-01-01 --date-to 2025-12-31
```

Los archivos se guardan en `backend/exports/`, carpeta excluida de Git.

## 8. Validación integral de la demo

```powershell
python scripts\validate_phase1_real_data.py
```

El script ejecuta el diagnóstico estructural, columnas críticas, demanda neta,
resúmenes anual y mensual, controles de calidad y una muestra de validación de
moneda. Genera:

- `exports/phase1_validation_report.json`
- `exports/phase1_monthly_summary.csv`
- `exports/phase1_data_issues.csv`

La validación inspecciona únicamente tablas y columnas presentes en la demo;
cuenta relaciones huérfanas, nulos, cantidades negativas, meses distintos y
artículos con al menos doce meses de historial.

## 9. Ejecutar pruebas

```powershell
pytest
```

Las pruebas actuales no requieren conexión ni credenciales reales.

## 10. Análisis exploratorio y ABC/XYZ

```powershell
python scripts\run_eda_analysis.py
python scripts\run_abc_xyz_analysis.py
```

Ambos scripts aceptan opcionalmente `--date-from`, `--date-to`, `--item-code`,
`--item-group`, `--warehouse-code` y `--min-months`.

Endpoints disponibles:

- `GET /analytics/data-quality`
- `GET /analytics/abc`
- `GET /analytics/abc-value`
- `GET /analytics/xyz`
- `GET /analytics/abc-xyz`
- `GET /analytics/summary`

Los endpoints admiten los mismos filtros. `/analytics/abc` también acepta
`abc_basis=quantity|amount`; cantidad es el criterio principal.

## 11. Forecast y comparación de modelos

```powershell
python scripts\run_forecast_baseline.py
python scripts\run_forecast_model_comparison.py
```

Opciones principales:

- `--test-months 6`: últimos meses reservados para backtesting.
- `--horizon 3|6`: horizonte futuro.
- `--date-from`, `--date-to`, `--item-group`, `--warehouse-code`.

Endpoints:

- `GET /forecast/candidates`
- `GET /forecast/summary`
- `GET /forecast/models`
- `GET /forecast/results`
- `GET /forecast/item/{item_code}`
- `GET /forecast/comparison`

La primera llamada completa puede tardar porque entrena y compara modelos. Los
resultados se mantienen en caché durante la ejecución del proceso FastAPI.

## 12. Inventario y reposición

```powershell
python scripts\run_replenishment_analysis.py
python scripts\export_replenishment_dashboard_data.py
```

Endpoints:

- `GET /inventory/current`
- `GET /replenishment/summary`
- `GET /replenishment/suggestions`
- `GET /replenishment/critical`
- `GET /replenishment/overstock`
- `GET /replenishment/item/{item_code}`
- `GET /replenishment/export-preview`

La reposición agrega almacenes cuando no se indica `warehouse_code`. Las
recomendaciones de confianza baja son referenciales y requieren revisión
humana; no se presentan como decisiones automáticas.
