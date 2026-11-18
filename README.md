# PayFast

**Plataforma académica de financiación colaborativa P2P (peer-to-peer)**
**Proyecto final · Ingeniería de Software**


[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/Uso-académico-informational)](#alcance-y-limitaciones)

**Aplicación:** https://payfast-web.onrender.com
**API:** https://payfast-6iv9.onrender.com
**Swagger:** https://payfast-6iv9.onrender.com/docs

---

## Equipo de desarrollo

PayFast fue desarrollado como proyecto académico para la asignatura **Ingeniería de Software**, del programa de **Ciencias de la Computación e Inteligencia Artificial**.

- Lina Castañeda
- Gerardo Ropero
- Juan Vasquez
- Santiago Rodriguez

## Tabla de contenido

1. [Descripción y objetivos](#descripción-y-objetivos)
2. [Actores y funcionalidades](#actores-y-funcionalidades)
3. [Tecnologías](#tecnologías)
4. [Arquitectura](#arquitectura)
5. [Estructura del repositorio](#estructura-del-repositorio)
6. [Modelo de datos](#modelo-de-datos)
7. [Estados y reglas de negocio](#estados-y-reglas-de-negocio)
8. [Flujos de operación](#flujos-de-operación)
9. [Instalación y ejecución local](#instalación-y-ejecución-local)
10. [API REST](#api-rest)
11. [Pruebas y calidad](#pruebas-y-calidad)
12. [Seguridad y consistencia](#seguridad-y-consistencia)
13. [Despliegue](#despliegue)
14. [Solución de problemas](#solución-de-problemas)
15. [Alcance y limitaciones](#alcance-y-limitaciones)

## Descripción y objetivos

PayFast conecta a **emprendedores** que solicitan microcréditos con **prestamistas** que financian esas solicitudes mediante aportes de saldo simulado. El sistema cubre el ciclo desde el registro del usuario hasta el desembolso y la consulta de movimientos de billetera.

**Objetivo general:** construir un prototipo cliente-servidor que aplique principios de ingeniería de software, diseño de API REST, persistencia relacional, autenticación, validaciones de negocio y pruebas automatizadas.

**Objetivos específicos:**

- Separar interfaz, API, servicios de negocio y persistencia.
- Modelar las transiciones permitidas de una solicitud de crédito.
- Evitar saldos negativos, aportes superiores al saldo pendiente y desembolsos duplicados.
- Registrar recargas, aportes y desembolsos para su consulta por el usuario autenticado.
- Permitir ejecutar y desplegar el sistema de forma reproducible.

## Actores y funcionalidades

| Actor | Funciones principales |
|---|---|
| **Emprendedor** | Crear billetera, recargar saldo simulado, crear solicitudes, consultar evaluaciones, solicitar evaluación, desembolsar solicitudes financiadas y consultar movimientos. |
| **Prestamista** | Crear billetera, recargar saldo simulado, explorar y filtrar solicitudes elegibles, aportar saldo y consultar movimientos. |
| **Administrador** | Rol previsto en el modelo de autorización; no se documenta aquí un panel administrativo funcional. |

### Funcionalidades implementadas

- Registro, inicio de sesión y perfil autenticado mediante JWT.
- Billetera principal individual en pesos colombianos (COP).
- Recargas simuladas, configurables por entorno.
- Solicitudes de crédito con monto, plazo, propósito y estado.
- Evaluación de riesgo a través de un servicio de buró simulado.
- Catálogo de solicitudes elegibles con filtros.
- Aportes de prestamistas y actualización del monto financiado.
- Desembolso simulado al emprendedor cuando la solicitud está financiada.
- Historial unificado de movimientos: recargas, aportes y desembolsos.
- Notificaciones de interfaz y presentación monetaria en COP.

## Tecnologías

| Capa | Tecnología | Función |
|---|---|---|
| Frontend | HTML5, CSS3, JavaScript ES Modules | Interfaz y comunicación HTTP |
| Backend | Python, FastAPI | API REST, dependencias y validaciones |
| Persistencia | PostgreSQL, SQLAlchemy 2.x | Almacenamiento y ORM |
| Migraciones | Alembic | Evolución versionada del esquema |
| Validación/configuración | Pydantic, pydantic-settings | Esquemas y variables de entorno |
| Autenticación | PyJWT, pwdlib/Argon2 | Tokens y contraseñas hasheadas |
| Pruebas | Pytest | Pruebas automatizadas del backend |
| Infraestructura | Docker Compose, Render | Base de datos local y despliegue |
| Control de versiones | Git, GitHub | Historial de cambios |

> El archivo `backend/requirements.txt` es la referencia para instalar las dependencias Python. El `docker-compose.yml` del proyecto utiliza **PostgreSQL 17** para el contenedor local.

## Arquitectura

### Diagrama de contenedores

```mermaid
flowchart TB
    U[Usuario: emprendedor o prestamista]
    F[Frontend estático<br/>HTML · CSS · JavaScript]
    API[API REST<br/>FastAPI]
    AUTH[Autenticación<br/>JWT y roles]
    S[Servicios de negocio<br/>billeteras · créditos · riesgo · aportes · desembolsos]
    ORM[SQLAlchemy ORM]
    DB[(PostgreSQL)]
    EXT[Buró y pasarela<br/>simulados]

    U -->|Navegador| F
    F -->|HTTPS / JSON + Bearer JWT| API
    API --> AUTH
    API --> S
    AUTH --> ORM
    S --> ORM
    ORM --> DB
    S --> EXT
```

### Capas del backend

```mermaid
flowchart LR
    A[api/<br/>Rutas HTTP] --> B[schemas/<br/>Validación y respuesta]
    A --> C[services/<br/>Reglas de negocio]
    C --> D[models/<br/>Entidades ORM]
    D --> E[db/<br/>Sesiones y conexión]
    E --> F[(PostgreSQL)]
    C --> G[domain/states.py<br/>Máquina de estados]
    H[core/<br/>Configuración y seguridad] -.-> A
    H -.-> C
```

**Responsabilidades:** `api/` gestiona HTTP y permisos; `schemas/` valida entradas/salidas; `services/` implementa las reglas; `models/` representa las tablas; `db/` administra sesiones; `domain/` define transiciones; `core/` centraliza configuración y seguridad.

## Estructura del repositorio

```text
payfast/
├── backend/
│   ├── app/
│   │   ├── api/                 # Rutas, autenticación y dependencias
│   │   ├── core/                # Configuración y seguridad
│   │   ├── db/                  # Base declarativa y sesiones
│   │   ├── domain/              # Estados y transiciones
│   │   ├── models/              # Entidades SQLAlchemy
│   │   │   └── wallet_topup.py  # Registro de recargas simuladas
│   │   ├── schemas/             # Modelos Pydantic
│   │   ├── services/            # Lógica de negocio
│   │   │   └── wallet_movements_service.py
│   │   └── main.py              # Aplicación FastAPI
│   ├── migrations/
│   │   └── versions/            # Versiones Alembic
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── css/styles.css
│   ├── js/
│   │   ├── api.js              # Cliente HTTP
│   │   ├── app.js              # Acceso, perfil y billetera
│   │   ├── auth.js             # Sesión
│   │   ├── config.js           # URL de la API
│   │   └── financing.js        # Solicitudes, aportes y movimientos
│   └── index.html
├── tests/                       # Pruebas Pytest
├── docs/                        # Documentación complementaria / UML
├── .env.example                 # Variables de ejemplo
├── docker-compose.yml           # PostgreSQL local
├── pytest.ini
└── README.md
```

## Modelo de datos

### Diagrama entidad-relación


```mermaid
erDiagram
    usuario ||--o{ usuario_rol : tiene
    rol ||--o{ usuario_rol : asignado
    usuario ||--o{ billetera : posee
    usuario ||--o{ solicitud_credito : solicita
    usuario ||--o{ aportes : realiza
    solicitud_credito ||--o{ evaluacion_riesgo : recibe
    solicitud_credito ||--o{ aportes : recibe
    solicitud_credito ||--o{ transacciones : origina
    billetera ||--o{ transacciones : recibe
    billetera ||--o{ recargas_billetera : registra

    usuario {
        uuid id PK
        varchar nombre
        varchar correo UK
        varchar password_hash
        boolean activo
        timestamp creado_en
    }
    rol {
        uuid id PK
        varchar nombre UK
    }
    usuario_rol {
        uuid usuario_id PK,FK
        uuid rol_id PK,FK
    }
    billetera {
        uuid id PK
        uuid usuario_id FK
        varchar tipo
        varchar moneda
        decimal saldo
        boolean activa
        timestamp creada_en
    }
    solicitud_credito {
        uuid id PK
        uuid usuario_id FK
        decimal monto
        decimal monto_financiado
        int plazo_meses
        varchar proposito
        varchar estado
        timestamp creada_en
    }
    evaluacion_riesgo {
        uuid id PK
        uuid solicitud_id FK
        varchar resultado
        int puntaje
        json datos_buro
        varchar detalle_error
        timestamp evaluada_en
    }
    aportes {
        uuid id PK
        uuid solicitud_id FK
        uuid prestamista_id FK
        decimal monto
        timestamp creado_en
    }
    transacciones {
        uuid id PK
        uuid solicitud_id FK
        uuid billetera_id FK
        decimal monto
        varchar estado
        varchar referencia_pasarela
        timestamp fecha
    }
    recargas_billetera {
        uuid id PK
        uuid billetera_id FK
        decimal monto
        timestamp creada_en
    }
```

### Diccionario de datos

Las siguientes definiciones reflejan los modelos existentes en el repositorio y los archivos locales incorporados para el historial. **PK** = clave primaria; **FK** = clave foránea; **UK** = valor único.

#### `usuario`

| Columna | Tipo SQLAlchemy | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `nombre` | VARCHAR(120) | Obligatorio |
| `correo` | VARCHAR(255) | Obligatorio, único, indexado |
| `password_hash` | VARCHAR(255) | Hash, nunca contraseña en texto plano |
| `activo` | BOOLEAN | Estado de la cuenta |
| `creado_en` | TIMESTAMP con zona | Fecha de creación |

#### `rol` y `usuario_rol`

| Tabla | Columnas | Regla |
|---|---|---|
| `rol` | `id` UUID; `nombre` VARCHAR(30) | `id` PK, `nombre` único |
| `usuario_rol` | `usuario_id`, `rol_id` UUID | PK compuesta y FKs con borrado en cascada |

#### `billetera`

| Columna | Tipo | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `usuario_id` | UUID | FK a `usuario` |
| `tipo` | VARCHAR(30) | Predeterminado: `principal` |
| `moneda` | VARCHAR(3) | Predeterminado: `COP` |
| `saldo` | NUMERIC(18,2) | Predeterminado 0; `saldo >= 0` |
| `activa` | BOOLEAN | Predeterminado `true` |
| `creada_en` | TIMESTAMP con zona | Fecha de creación |

Restricción única: (`usuario_id`, `tipo`), para evitar dos billeteras principales del mismo usuario.

#### `solicitud_credito`

| Columna | Tipo | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `usuario_id` | UUID | FK al emprendedor |
| `monto` | NUMERIC(18,2) | Mayor que 0 |
| `monto_financiado` | NUMERIC(18,2) | Entre 0 y `monto` |
| `plazo_meses` | INTEGER | Mayor que 0 |
| `proposito` | VARCHAR(500) | Obligatorio |
| `estado` | VARCHAR(40) | Estado de la solicitud |
| `creada_en` | TIMESTAMP con zona | Fecha de creación |

#### `evaluacion_riesgo`

| Columna | Tipo | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `solicitud_id` | UUID | FK a solicitud |
| `resultado` | VARCHAR(20) | Resultado de evaluación |
| `puntaje` | INTEGER, nullable | Entre 0 y 100 si existe |
| `datos_buro` | JSON, nullable | Datos del simulador |
| `detalle_error` | VARCHAR(500), nullable | Motivo del fallo |
| `evaluada_en` | TIMESTAMP con zona | Fecha de evaluación |

#### `aportes`

| Columna | Tipo | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `solicitud_id` | UUID | FK a solicitud |
| `prestamista_id` | UUID | FK a usuario |
| `monto` | NUMERIC(18,2) | Mayor que 0 |
| `creado_en` | TIMESTAMP con zona | Fecha del aporte |

#### `transacciones`

| Columna | Tipo | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `solicitud_id` | UUID | FK a solicitud |
| `billetera_id` | UUID | FK a billetera receptora |
| `monto` | NUMERIC(18,2) | Mayor que 0 |
| `estado` | Enum (`PENDIENTE`, `EXITOSA`, `FALLIDA`) | Resultado de la operación |
| `referencia_pasarela` | VARCHAR(100), nullable | Única cuando existe |
| `fecha` | TIMESTAMP con zona | Fecha de transacción |

Existe un índice único parcial que impide registrar **más de un desembolso exitoso por solicitud**.

#### `recargas_billetera` — nueva funcionalidad

| Columna | Tipo | Regla / significado |
|---|---|---|
| `id` | UUID | PK |
| `billetera_id` | UUID | FK a billetera |
| `monto` | NUMERIC(18,2) | Importe acreditado |
| `creada_en` | TIMESTAMP con zona | Fecha de recarga |

La tabla se introduce mediante la migración Alembic `33adc9039dc8_create_wallet_topups.py`. El registro de recarga y la actualización del saldo se efectúan dentro de la misma operación de base de datos.


## Estados y reglas de negocio

### Ciclo de vida de la solicitud

```mermaid
stateDiagram-v2
    [*] --> PENDIENTE_EVALUACION
    PENDIENTE_EVALUACION --> EVALUADA: evaluación favorable
    PENDIENTE_EVALUACION --> RECHAZADA: evaluación desfavorable
    EVALUADA --> EN_FINANCIACION: primer aporte parcial
    EVALUADA --> FINANCIADA: aporte cubre el total
    EN_FINANCIACION --> FINANCIADA: se completa el monto
    FINANCIADA --> DESEMBOLSADA: desembolso exitoso
    RECHAZADA --> [*]
    DESEMBOLSADA --> [*]
```

Las transiciones autorizadas se encuentran en `backend/app/domain/states.py`. No se permite desembolsar una solicitud que no esté `FINANCIADA`.

### Estado de las transacciones

```mermaid
stateDiagram-v2
    [*] --> PENDIENTE
    PENDIENTE --> EXITOSA
    PENDIENTE --> FALLIDA
    FALLIDA --> PENDIENTE: reintento permitido
```

### Reglas de integridad relevantes

1. La billetera principal es única por usuario y tipo; el saldo nunca debe ser negativo.
2. Los montos monetarios se almacenan como `NUMERIC(18,2)` y se procesan con `Decimal` en Python.
3. El monto financiado debe permanecer entre cero y el monto solicitado.
4. Los aportes requieren saldo disponible y no pueden superar el monto pendiente de la solicitud.
5. El desembolso requiere que la solicitud esté financiada y que el destinatario sea su propietario.
6. Una solicitud no puede tener dos desembolsos exitosos.
7. Las recargas simuladas requieren `ENABLE_DEMO_TOPUPS=true` y están limitadas a **10.000.000 COP por operación**.
8. Las operaciones sobre billeteras y solicitudes emplean transacciones de base de datos y bloqueos de fila en PostgreSQL cuando corresponde.

## Flujos de operación

### Flujo completo de financiación

```mermaid
sequenceDiagram
    autonumber
    actor E as Emprendedor
    participant FE as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    actor P as Prestamista
    participant SIM as Servicios simulados

    E->>FE: Crear solicitud
    FE->>API: POST /credit-requests/
    API->>DB: Guardar PENDIENTE_EVALUACION
    DB-->>API: Solicitud creada
    API-->>FE: 201 Created
    E->>FE: Evaluar solicitud
    FE->>API: POST /credit-requests/{id}/risk-evaluations
    API->>SIM: Consultar buró simulado
    SIM-->>API: Puntaje / resultado
    API->>DB: Registrar evaluación y estado
    P->>FE: Consultar catálogo y aportar
    FE->>API: GET /credit-requests/eligible
    FE->>API: POST /credit-requests/{id}/contributions
    API->>DB: Debitar billetera + registrar aporte + actualizar financiación
    DB-->>API: Confirmación
    API-->>FE: 201 Created
    E->>FE: Desembolsar solicitud financiada
    FE->>API: POST /credit-requests/{id}/disburse
    API->>SIM: Pasarela simulada
    SIM-->>API: Resultado
    API->>DB: Registrar transacción y acreditar billetera
    API-->>FE: 200 OK
    FE->>API: GET /wallets/me/movements
    API-->>FE: Historial de movimientos
```

### Recarga e historial de movimientos

```mermaid
flowchart TD
    A[Usuario autenticado] --> B[Introduce monto de recarga]
    B --> C{Recargas habilitadas<br/>y monto válido?}
    C -- No --> D[Mostrar error; sin acreditar saldo]
    C -- Sí --> E[POST /wallets/me/top-up]
    E --> F[Transacción en PostgreSQL]
    F --> G[Incrementar saldo]
    G --> H[Registrar recarga]
    H --> I[Confirmar transacción]
    I --> J[Actualizar saldo e historial]
    J --> K[GET /wallets/me/movements]
    K --> L[Mostrar ingresos y egresos en COP]
```

### Interpretación del historial

| Tipo | Dirección | Signo visual | Origen del dato |
|---|---|---|---|
| `RECARGA` | `INGRESO` | `+` | `recargas_billetera` |
| `APORTE` | `EGRESO` | `−` | `aportes` |
| `DESEMBOLSO` exitoso | `INGRESO` | `+` | `transacciones` |
| `DESEMBOLSO` fallido | Sin movimiento monetario efectivo | Sin signo | `transacciones` |

El endpoint de historial agrupa los registros de estas entidades y los devuelve para el usuario autenticado.

## Instalación y ejecución local

### Requisitos

- Git.
- Python compatible con `backend/requirements.txt` (entorno de desarrollo utilizado: **Python 3.14**).
- Docker Engine y Docker Compose **o** PostgreSQL instalado localmente.
- Navegador moderno.


### 1. Clonar el proyecto

```bash
git clone https://github.com/SantiagoRodriguez114/PayFast.git
cd PayFast
```

### 2. Crear el entorno Python

**Bash / Zsh:**

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m pip install pytest
```

`pytest` se instala por separado porque no figura en el `backend/requirements.txt` de ejecución consultado.

### 3. Crear las variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y utiliza contraseñas locales propias. Ejemplo de **desarrollo** (no apto para producción):

```dotenv
POSTGRES_USER=payfast_user
POSTGRES_PASSWORD=CAMBIAR_POR_CLAVE_LOCAL
POSTGRES_DB=payfast_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://payfast_user:CAMBIAR_POR_CLAVE_LOCAL@127.0.0.1:5432/payfast_db
SECRET_KEY=GENERAR_UN_SECRETO_ALEATORIO_LARGO
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENABLE_DEMO_TOPUPS=true
FRONTEND_ORIGIN=http://127.0.0.1:5500
```

Genera una clave de desarrollo con:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

**Importante:** `POSTGRES_PASSWORD` y la contraseña incluida en `DATABASE_URL` deben coincidir. Nunca subas `.env` a GitHub.

### 4. Levantar PostgreSQL

Con Docker Compose:

```bash
docker compose up -d db
docker compose ps
```

El contenedor expone PostgreSQL en `127.0.0.1:5432` por defecto y mantiene sus datos en el volumen `payfast_pgdata`. Si ya tienes PostgreSQL local usando ese puerto, detén uno de los servicios o cambia `POSTGRES_PORT` y la URL de conexión.

Si prefieres PostgreSQL instalado directamente, crea una base y un usuario equivalentes a los valores del `.env` y **no** ejecutes Docker Compose.

### 5. Aplicar migraciones

```bash
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini current
```

Este paso crea y actualiza las tablas según las migraciones versionadas. La migración del historial de recargas debe estar incluida en la rama que ejecutes.

### 6. Iniciar la API

**Terminal A** (con entorno virtual activo):

```bash
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Comprobar:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/database
```

Documentación interactiva: http://127.0.0.1:8000/docs

### 7. Configurar el frontend para desarrollo

El archivo `frontend/js/config.js` del repositorio apunta al backend desplegado. Para probar **tu backend local**, cambia temporalmente su contenido a:

```javascript
window.PAYFAST_API_URL = "http://127.0.0.1:8000";
```

**Terminal B:**

```bash
python -m http.server 5500 --directory frontend
```

Abre http://127.0.0.1:5500. Mantén **ambas terminales** abiertas durante las pruebas.


```bash
git restore frontend/js/config.js
```

Comprueba que vuelva a contener:

```javascript
window.PAYFAST_API_URL = "https://payfast-6iv9.onrender.com";
```

### 8. Primera demostración funcional

1. Registrar un emprendedor y un prestamista.
2. Iniciar sesión con cada cuenta y crear su billetera principal.
3. Realizar una recarga simulada al prestamista.
4. Crear una solicitud desde el emprendedor y evaluarla.
5. Entrar como prestamista, localizar la solicitud elegible y aportar.
6. Completar la financiación y desembolsar desde la cuenta del emprendedor.
7. Verificar saldo e historial de movimientos de ambas cuentas.

## API REST

Las rutas que requieren sesión utilizan `Authorization: Bearer <TOKEN>`.

| Método | Ruta | Uso principal |
|---|---|---|
| `GET` | `/` | Información básica de la API |
| `GET` | `/health` | Salud del servicio |
| `GET` | `/health/database` | Conexión a base de datos |
| `POST` | `/auth/register` | Registrar usuario |
| `POST` | `/auth/login` | Obtener token JWT |
| `GET` | `/auth/me` | Consultar perfil autenticado |
| `POST` | `/wallets/` | Crear billetera principal |
| `GET` | `/wallets/me` | Consultar billetera |
| `POST` | `/wallets/me/top-up` | Recarga simulada |
| `GET` | `/wallets/me/movements` | Historial unificado |
| `POST` | `/credit-requests/` | Crear solicitud |
| `GET` | `/credit-requests/me` | Solicitudes propias |
| `GET` | `/credit-requests/{id}` | Detalle de solicitud propia |
| `GET` | `/credit-requests/eligible` | Catálogo filtrable para prestamistas |
| `POST` | `/credit-requests/{id}/risk-evaluations` | Evaluar solicitud |
| `GET` | `/credit-requests/{id}/risk-evaluations` | Historial de evaluaciones |
| `POST` | `/credit-requests/{id}/contributions` | Aportar a solicitud |
| `POST` | `/credit-requests/{id}/disburse` | Desembolsar solicitud |
| `GET` | `/credit-requests/transactions/me` | Historial específico de desembolsos |

### Ejemplo: autenticación y consulta de movimientos

```bash
# 1. Iniciar sesión (credenciales de prueba creadas previamente)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"correo":"usuario@example.com","password":"CLAVE_DE_PRUEBA"}'

# 2. Copiar el access_token de la respuesta y usarlo en la petición
curl http://127.0.0.1:8000/wallets/me/movements \
  -H 'Authorization: Bearer REEMPLAZAR_TOKEN'
```

**Ejemplo ilustrativo de movimiento** (campos utilizados por la interfaz):

```json
{
  "id": "uuid-del-movimiento",
  "tipo": "RECARGA",
  "direccion": "INGRESO",
  "monto": "100000.00",
  "estado": "EXITOSA",
  "fecha": "2026-11-18T11:00:00Z",
  "solicitud_id": null,
  "referencia": null
}
```

El endpoint devuelve una **lista** de objetos con esta estructura. Consulta `/docs` para los esquemas publicados por la versión desplegada.

## Pruebas y calidad

Desde la raíz, con `.venv` activo:

```bash
pytest -q --tb=short
node --check frontend/js/app.js
node --check frontend/js/api.js
node --check frontend/js/financing.js
git diff --check
```

## Seguridad y consistencia

- Las contraseñas se almacenan mediante hashes, no en texto plano.
- La autenticación usa JWT y el backend comprueba identidad/permisos para las operaciones protegidas.
- Las variables sensibles (`SECRET_KEY`, credenciales de PostgreSQL) pertenecen al entorno y no al repositorio.
- La API aplica restricciones de validación; el frontend no es una barrera de seguridad.
- El tipo `NUMERIC(18,2)` y `Decimal` evita usar números binarios de punto flotante para saldos persistidos.
- Las operaciones que modifican saldo utilizan transacciones y, en PostgreSQL, bloqueos de fila cuando corresponde.
- La base de datos contiene restricciones para impedir saldos negativos, financiación excesiva y desembolsos exitosos duplicados.
- Las recargas de demostración deben desactivarse en cualquier entorno que no sea exclusivamente académico.

## Despliegue

### Topología

```mermaid
flowchart LR
    B[Navegador] -->|HTTPS| W[Render Static Site<br/>payfast-web]
    W -->|HTTPS API| A[Render Web Service<br/>payfast API]
    A -->|SQL| P[(Render PostgreSQL<br/>payfast-db)]
```

| Componente | Dirección / configuración |
|---|---|
| Frontend | https://payfast-web.onrender.com |
| Backend | https://payfast-6iv9.onrender.com |
| Documentación | https://payfast-6iv9.onrender.com/docs |
| Base de datos | PostgreSQL administrado en Render |

**Comando de inicio del backend:**

```bash
alembic -c backend/alembic.ini upgrade head && uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

**Variables relevantes del backend:** `DATABASE_URL`, `SECRET_KEY`, `FRONTEND_ORIGIN`, `ENABLE_DEMO_TOPUPS` y, cuando aplique, `ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES`.

La URL del frontend autorizado debe corresponder a `FRONTEND_ORIGIN=https://payfast-web.onrender.com`. La URL del backend en `frontend/js/config.js` debe ser la de Render antes de publicar.

### Lista de verificación de despliegue

1. Ejecutar pruebas y comprobaciones de sintaxis.
2. Revisar `git status` y no incluir `.env`, tokens ni secretos.
3. Confirmar que la migración `33adc9039dc8` está versionada.
4. Confirmar que `frontend/js/config.js` apunta al backend de Render.
5. Hacer commit y push a `main`.
6. Verificar en los logs que Alembic ejecutó las migraciones y que Uvicorn inició.
7. Probar autenticación, recarga, aporte, desembolso e historial desde la URL pública.

## Solución de problemas

| Síntoma | Comprobación / solución |
|---|---|
| `ModuleNotFoundError: app` | Iniciar Uvicorn con `--app-dir backend` desde la raíz. |
| `Connection refused` a PostgreSQL | Verificar `docker compose ps`, `DATABASE_URL` y puerto. |
| Alembic no encuentra configuración | Usar `alembic -c backend/alembic.ini ...`. |
| CORS bloquea solicitudes | Revisar origen del frontend y `FRONTEND_ORIGIN`. |
| El frontend público no conecta | Comprobar `frontend/js/config.js`; no debe apuntar a `127.0.0.1`. |
| `Identifier ... has already been declared` | Buscar importaciones y declaraciones duplicadas en el mismo módulo. |
| El historial devuelve error | Revisar la respuesta de `GET /wallets/me/movements` y logs del backend. |
| Recarga acreditada, pero historial no actualizado | Consultar el saldo antes de reintentar; evitar duplicar operaciones. |
| `403` al recargar | Comprobar `ENABLE_DEMO_TOPUPS`. |
| `401` | Iniciar sesión de nuevo; el token puede haber expirado. |

## Alcance y limitaciones

PayFast demuestra un flujo de financiación P2P en un entorno controlado. **No incluye**, por el solo hecho de tener estas funcionalidades, integración bancaria real, custodia de fondos, verificación de identidad regulatoria, prevención de lavado de activos, cobro de cuotas, gestión de mora ni garantías de disponibilidad comercial.

El buró de riesgo y la pasarela son simuladores. Los resultados no deben utilizarse para decisiones crediticias reales.

Para extenderlo a un sistema financiero real harían falta, entre otros, análisis jurídico y regulatorio en Colombia, controles de seguridad adicionales, auditoría, observabilidad, reconciliación contable, manejo de incidentes y pruebas de carga.

---

**Repositorio:** https://github.com/SantiagoRodriguez114/PayFast
**Contexto:** proyecto académico de Ingeniería de Software.