# Despliegue seguro

## Arquitectura recomendada

Despliegue el frontend React como proyecto Vercel con raíz `frontend/` y el
backend FastAPI como Azure Container App o Azure App Service en `Brazil South`.
El backend es el único componente que accede a Azure SQL. El Dockerfile instala
ODBC Driver 18 en un runtime Linux controlado.

Vercel soporta Python Functions, pero su documentación no garantiza la
instalación de `unixODBC`/`msodbcsql18` ni el comportamiento de `pyodbc` en ese
runtime. Además, el plan y la configuración de cuenta necesarios para Static
IPs o Secure Compute no se pueden comprobar desde este repositorio. Por eso no
se prepara un backend SQL Server en Vercel ni se abre el firewall a rangos
dinámicos. Si la cuenta tiene Vercel Static IPs o Secure Compute, debe validarse
primero un build y una conexión real; entonces se puede mover el backend con el
rango asignado por Vercel.

## Variables del backend

Configurelas como secretos/variables del servicio, nunca en el repositorio:

```env
DB_SERVER=<AZURE_SQL_SERVER>
DB_PORT=1433
DB_NAME=<AZURE_SQL_DATABASE>
DB_USER=<READ_ONLY_USER>
DB_PASSWORD=<SECRET_MANAGER_VALUE>
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERTIFICATE=no
DB_CONNECTION_TIMEOUT=60
DATA_PROVIDER=demo
APP_ENV=production
ALLOWED_ORIGINS=https://<VERCEL_PROJECT>.vercel.app
```

`DB_PASSWORD` debe existir antes de iniciar la aplicación. No se registra y no
se devuelve en excepciones. `portal_demo_reader` debe conservar permisos
SELECT y no tener INSERT, UPDATE ni DELETE.

## Variables del frontend

```env
VITE_API_URL=https://<BACKEND_HOST>
```

No configure `VITE_DB_*`: cualquier variable `VITE_` queda expuesta al
navegador.

## Firewall de Azure SQL

No usar `0.0.0.0–255.255.255.255` ni habilitar “Allow Azure services” como
solución general.

Para Azure App Service sin NAT, autorice en Azure SQL todas las direcciones
`possibleOutboundIpAddresses` del App Service (son un conjunto que puede
cambiar). La opción más estable es integración VNet + NAT Gateway con una IP
pública reservada; en ese caso autorice únicamente `<NAT_PUBLIC_IP>/32`.

Para Vercel, solo autorice el par/rango exacto que aparezca en el proyecto en
Settings → Networking después de contratar y activar Static IPs, o la red
privada definida por Secure Compute. El repositorio no puede conocer esas IPs
ni crear la regla sin autorización explícita.

## Build y prueba local

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm run build

cd ../backend
python -m pip install -r requirements.txt
ruff check app tests scripts
pytest -q
python scripts/verify_demo_connection.py
# Prueba opcional contra Azure SQL (solo lectura):
RUN_AZURE_INTEGRATION=1 pytest -q -m integration
```

El preflight hace DNS, TCP 1433, login, `DB_NAME()`, `SUSER_SNAME()` y prueba
de permisos sin escribir en la base. El diagnóstico estructural es:

```bash
python scripts/diagnose_sap_db.py
```

## Procedimiento de despliegue

1. Cree el backend en Brazil South y configure sus variables en el servicio.
2. Configure el health check del servicio en `/api/health`.
3. Autorice solo la IP fija de NAT o las IPs de salida reales del servicio.
4. Ejecute `/api/health/db` y `/sap/diagnostics/schema` desde una red autorizada.
5. Cree el proyecto Vercel con raíz `frontend/`, `VITE_API_URL` y
   `frontend/vercel.json`.
6. Configure en Azure `ALLOWED_ORIGINS` con el dominio Vercel exacto, sin `*`.

## Prueba posterior al despliegue

```bash
curl -fsS https://<BACKEND_HOST>/api/health
curl -fsS https://<BACKEND_HOST>/api/health/db
curl -fsS https://<BACKEND_HOST>/sap/diagnostics/schema
curl -fsS https://<VERCEL_PROJECT>.vercel.app/
```

Si Azure SQL está reactivándose, la API responde 503 controlado y el frontend
ofrece reintentar.

## Rollback

Conserve la última imagen/container revision y el último deployment Vercel
conocidos como buenos. Revierta primero el backend a la revisión anterior,
verifique `/api/health/db`, y después revierta el frontend a la versión anterior.
No elimine reglas de firewall durante un rollback; retire una IP antigua solo
después de verificar que la nueva salida funciona y que no hay tráfico legítimo.
