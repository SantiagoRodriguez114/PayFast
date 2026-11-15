# Módulo de Solicitudes de Crédito

## 1. Objetivo

Este módulo permite que los emprendedores autenticados registren solicitudes de microcrédito y consulten su información y estado dentro de la plataforma PayFast.

La funcionalidad implementa los requisitos relacionados con la creación y consulta de solicitudes de crédito (HU-03 y HU-04).

## 2. Endpoints disponibles

Todos los endpoints requieren autenticación mediante un token JWT de acceso.

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/credit-requests/` | Registra una nueva solicitud de crédito. |
| GET | `/credit-requests/me` | Consulta las solicitudes del usuario autenticado. |
| GET | `/credit-requests/{solicitud_id}` | Consulta una solicitud específica del usuario autenticado. |

## 3. Reglas de negocio

- El usuario debe estar autenticado para registrar o consultar solicitudes.
- El emprendedor debe tener una billetera activa para registrar una solicitud.
- Cada solicitud queda asociada al usuario autenticado.
- El estado inicial de una solicitud es `pendiente_evaluacion`.
- La creación de una solicitud no implica su aprobación.
- Registrar una solicitud no modifica el saldo de la billetera.
- Un usuario solamente puede consultar sus propias solicitudes.
- Las solicitudes se muestran ordenadas por fecha de creación, de la más reciente a la más antigua.

## 4. Validaciones de entrada

El endpoint de creación recibe los siguientes campos:

| Campo | Tipo | Validación |
|---|---|---|
| `monto` | Decimal | Debe ser mayor que cero y admite hasta dos decimales. |
| `plazo_meses` | Entero | Debe ser mayor que cero. |
| `proposito` | Texto | Obligatorio, entre 1 y 500 caracteres después de eliminar espacios externos. |

Los campos `usuario_id` y `estado` no pueden ser enviados por el cliente. Estos valores son controlados por el backend para evitar modificaciones no autorizadas.

Las solicitudes que incumplen las validaciones reciben una respuesta HTTP `422`.

## 5. Respuestas HTTP

| Código | Significado |
|---|---|
| 201 | Solicitud creada correctamente. |
| 200 | Consulta realizada correctamente. |
| 401 | Usuario no autenticado. |
| 404 | Solicitud inexistente o perteneciente a otro usuario. |
| 409 | El usuario no tiene una billetera activa para solicitar el crédito. |
| 422 | Los datos enviados no cumplen las validaciones. |

## 6. Seguridad y control de acceso

La identificación del propietario se obtiene del usuario autenticado mediante el token JWT. El backend no confía en identificadores de usuario enviados por el cliente.

Para las consultas individuales, el servicio verifica simultáneamente el identificador de la solicitud y el identificador del usuario autenticado. De esta manera, se evita que un usuario acceda a solicitudes pertenecientes a otras cuentas.

## 7. Persistencia de datos

Las solicitudes se almacenan en la tabla `solicitud_credito` de PostgreSQL.

Cada registro contiene:

- Identificador único UUID.
- Identificador del usuario propietario.
- Monto solicitado.
- Plazo en meses.
- Propósito del crédito.
- Estado de la solicitud.
- Fecha de creación.

La base de datos aplica restricciones para impedir montos y plazos menores o iguales a cero.