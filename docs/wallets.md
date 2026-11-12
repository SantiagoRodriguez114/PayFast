# Módulo de Billeteras — PayFast

## 1. Objetivo

El módulo de billeteras permite a los usuarios autenticados abrir y consultar una billetera digital dentro de PayFast.

La implementación utiliza una moneda simulada (COP). No se realizan movimientos de dinero real ni operaciones bancarias o criptoactivos.

## 2. Reglas de negocio

- Solo los usuarios autenticados pueden abrir una billetera.
- Cada usuario puede tener una única billetera de tipo principal.
- La billetera se crea con un saldo inicial de 0.00 COP.
- El saldo no puede ser negativo.
- El propietario se determina mediante el usuario autenticado y no mediante datos enviados por el cliente.
- Un usuario solamente puede consultar su propia billetera.
- Intentar crear una segunda billetera principal genera un conflicto.

Estas reglas representan decisiones técnicas provisionales del prototipo, pendientes de validación definitiva por el Product Owner.

## 3. Modelo de datos

### Billetera

| Atributo | Tipo | Descripción |
|---|---|---|
| id | UUID | Identificador único |
| usuario_id | UUID | Referencia al propietario |
| tipo | String(30) | Tipo de billetera |
| moneda | String(3) | Moneda simulada |
| saldo | Numeric(18,2) | Saldo disponible |
| activa | Boolean | Estado de la billetera |
| creada_en | DateTime | Fecha de creación |

### Restricciones de integridad

- Clave primaria sobre `id`.
- Clave foránea `usuario_id` hacia `usuario.id`.
- Restricción UNIQUE sobre `usuario_id` y `tipo`.
- Restricción CHECK para impedir saldos negativos.
- Eliminación en cascada cuando se elimina el usuario.

## 4. Endpoints

### POST /wallets/

Abre la billetera principal del usuario autenticado.

**Autenticación:** Bearer JWT.

**Respuesta exitosa:** HTTP 201 Created.

La API genera automáticamente el identificador, asigna el propietario autenticado y establece el saldo inicial en cero.

**Posibles respuestas:**

- 201: billetera creada.
- 401: usuario no autenticado.
- 409: ya existe una billetera principal.

### GET /wallets/me

Consulta la billetera principal del usuario autenticado.

**Autenticación:** Bearer JWT.

**Posibles respuestas:**

- 200: billetera encontrada.
- 401: usuario no autenticado.
- 404: el usuario todavía no tiene una billetera.

## 5. Arquitectura y responsabilidades

- `app/models/wallet.py`: modelo ORM y restricciones de datos.
- `app/schemas/wallet.py`: estructura de los datos expuestos por la API.
- `app/services/wallet_service.py`: reglas de creación y consulta.
- `app/api/wallets.py`: endpoints HTTP y manejo de respuestas.
- `app/api/dependencies.py`: identificación del usuario autenticado.
- `app/main.py`: registro del router.

La separación entre API, servicios y modelos permite mantener las reglas de negocio independientes de los detalles HTTP.

## 6. Seguridad e integridad

El backend no acepta el saldo ni el identificador del propietario como datos controlados por el cliente.

El propietario se obtiene del token JWT validado mediante `get_current_user`.

La aplicación comprueba previamente la existencia de una billetera. Adicionalmente, la restricción UNIQUE de PostgreSQL evita duplicados incluso ante solicitudes concurrentes.

Los valores monetarios se representan mediante Decimal y Numeric(18,2), evitando los problemas de precisión de los números de punto flotante.

## 7. Pruebas

Archivo: `tests/test_wallet_api.py`

Se implementaron seis pruebas:

1. Apertura de billetera sin autenticación.
2. Consulta de billetera sin autenticación.
3. Creación correcta con saldo inicial cero.
4. Prevención de billeteras principales duplicadas.
5. Consulta de la billetera del usuario.
6. Consulta cuando todavía no existe una billetera.

Las seis pruebas pasaron junto con la suite completa.