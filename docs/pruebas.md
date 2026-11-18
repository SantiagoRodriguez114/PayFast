# Estrategia y resultados de pruebas — PayFast

## 1. Objetivo

Verificar el comportamiento funcional y las reglas de negocio del backend de PayFast mediante pruebas automatizadas, con énfasis en autenticación, control de acceso, solicitudes, evaluación de riesgo, financiación y desembolsos simulados.

Este documento diferencia los escenarios comprobados de los requisitos que todavía no cuentan con evidencia de validación.

## 2. Herramientas y entorno

- **pytest:** ejecución de las pruebas automatizadas.
- **FastAPI `TestClient`:** peticiones HTTP de prueba a la aplicación.
- **SQLAlchemy:** creación de tablas y acceso a la base de prueba.
- **SQLite en memoria:** persistencia aislada para cada prueba.
- **PostgreSQL y Alembic:** base y migraciones del entorno de desarrollo, verificadas por separado.

### Aislamiento de pruebas

La fixture `client` de `tests/conftest.py` es automática (`autouse=True`). Para cada prueba:

1. Crea un motor SQLite en memoria con `StaticPool`.
2. Crea las tablas a partir de `Base.metadata`.
3. Inserta los roles `emprendedor` y `prestamista`.
4. Sobrescribe la dependencia `get_db` de FastAPI para utilizar la sesión de prueba.
5. Ejecuta la prueba mediante `TestClient(app)`.
6. Elimina la sobrescritura de dependencias, descarta las tablas y libera el motor.

Esta configuración evita modificar la base de desarrollo y reduce la contaminación de datos entre pruebas.

## 3. Organización de la suite

| Archivo | Área principal |
|---|---|
| `test_auth_api.py` | Registro e inicio de sesión |
| `test_auth_protected.py` | Autenticación de rutas protegidas |
| `test_auth_schemas.py` | Validación de entradas de autenticación |
| `test_security.py` | Contraseñas y tokens |
| `test_wallet_api.py` | Creación y consulta de billeteras |
| `test_credit_request_api.py` | Solicitudes de crédito |
| `test_risk_evaluation_api.py` | Evaluaciones de riesgo |
| `test_eligible_catalog_api.py` | Catálogo de solicitudes elegibles |
| `test_aporte_api.py` | Aportes y financiación |
| `test_desembolso_api.py` | Desembolsos y transacciones |
| `test_state_request.py` | Transiciones de solicitudes |
| `test_state_transaction.py` | Transiciones de transacciones |
| `test_health.py` | Estado general de la aplicación |
| `test_health_database.py` | Comprobación de conexión a la base de datos |

La distribución exacta de casos por archivo puede cambiar al ampliar la suite; no se fija aquí un conteo individual.

## 4. Escenarios relevantes

### Autenticación y autorización

Se prueban registro, credenciales inválidas, validación de esquemas, tokens y restricciones de acceso. Los detalles de cobertura y limitaciones de seguridad están en `docs/auth.md`.

### Solicitudes y evaluación de riesgo

Se comprueban la creación y consulta de solicitudes, el control de acceso por propietario y los resultados favorables, desfavorables y fallidos del buró simulado.

### Financiación

Las pruebas verifican el registro de aportes, el rechazo de montos superiores al saldo pendiente y la financiación completa con un solo aporte. Esta última comprueba el estado `FINANCIADA`, el monto financiado y el saldo restante de la billetera del prestamista.

Las pruebas del dominio contemplan la transición directa `EVALUADA → FINANCIADA`, necesaria cuando un único aporte cubre el total.

### Desembolsos

Los escenarios incluyen desembolso exitoso, consulta de transacciones, veinte reintentos **secuenciales** después de un éxito sin duplicar la acreditación y veinte rechazos **secuenciales** simulados de pasarela sin acreditar saldo.

## 5. Ejecución

Desde la raíz del proyecto, con el entorno virtual y dependencias instalados:

```bash
pytest -q --tb=short
```

Para ejecutar un módulo concreto:

```bash
pytest -q tests/test_aporte_api.py -v --tb=short
pytest -q tests/test_desembolso_api.py -v --tb=short
```

Para comprobar migraciones y formato del diff:

```bash
alembic -c backend/alembic.ini check
git diff --check
```

`alembic check` necesita una conexión funcional a la base configurada. No es una prueba de rendimiento ni un sustituto de la ejecución de migraciones en un entorno limpio.