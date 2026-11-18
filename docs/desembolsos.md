# Módulo de desembolsos y transacciones — PayFast

## 1. Objetivo

Permitir que un emprendedor reciba en su billetera el monto de una solicitud completamente financiada, mediante una pasarela bancaria simulada.

Este módulo implementa el desembolso asociado a HU-08.

## 2. Componentes

| Archivo | Responsabilidad |
|---|---|
| `backend/app/api/credit_requests.py` | Endpoints de desembolso y consulta de transacciones |
| `backend/app/services/desembolso_service.py` | Reglas de desembolso y actualización de saldos |
| `backend/app/services/pasarela_service.py` | Simulación de confirmación o rechazo |
| `backend/app/models/transaction.py` | Persistencia de transacciones financieras |
| `backend/app/models/wallet.py` | Saldo de la billetera del emprendedor |
| `backend/app/models/credit_request.py` | Estado y monto de la solicitud |

## 3. Endpoints

### POST `/credit-requests/{solicitud_id}/disburse`

Solicita el desembolso de una solicitud financiada.

El usuario autenticado debe ser el propietario de la solicitud.

### GET `/credit-requests/transactions/me`

Consulta las transacciones asociadas a las billeteras del usuario autenticado.

## 4. Reglas de negocio

Para realizar un desembolso:

1. La solicitud debe existir.
2. El usuario autenticado debe ser su propietario.
3. No debe existir una transacción exitosa previa.
4. La solicitud debe estar en estado `FINANCIADA`.
5. El emprendedor debe tener una billetera principal activa.
6. La pasarela simulada debe confirmar la operación.

Si la pasarela confirma el desembolso, el servicio registra una transacción `EXITOSA`, acredita el monto solicitado en la billetera y cambia el estado a `DESEMBOLSADA`.

Si la pasarela rechaza explícitamente la operación, registra una transacción `FALLIDA`, conserva el estado `FINANCIADA` y no modifica el saldo.

## 5. Pasarela simulada

`PasarelaBancariaService` recibe un monto y un identificador de cuenta destino.

Para montos positivos, su implementación estándar devuelve una confirmación simulada y una referencia con formato `TRX-SIM-...`.

Las pruebas pueden sustituir la respuesta de la pasarela para simular rechazos.

La pasarela no se conecta con instituciones financieras ni ejecuta movimientos de dinero real.

## 6. Consistencia e idempotencia

El servicio bloquea la solicitud y la billetera mediante `SELECT ... FOR UPDATE`, dentro de una transacción de base de datos.

En un desembolso exitoso, el registro de la transacción, el aumento del saldo y el cambio de estado se confirman conjuntamente.

La tabla `transacciones` contiene un índice único parcial denominado `uq_transacciones_desembolso_exitoso`, que permite como máximo una transacción `EXITOSA` por solicitud.

Los intentos fallidos pueden conservarse como registros separados.

## 7. Manejo de errores

Un rechazo explícito de la pasarela genera una transacción `FALLIDA` y no acredita dinero.

Una excepción inesperada durante la operación provoca un `rollback()` de los cambios no confirmados. No necesariamente queda un registro persistido de ese error.

En una integración bancaria real se necesitarían mecanismos adicionales de conciliación, recuperación ante fallos e identificación única de operaciones externas.

## 8. Pruebas

Archivo principal: `tests/test_desembolso_api.py`.

Las pruebas verifican:

- Desembolso exitoso.
- Consulta de transacciones del usuario.
- Veinte reintentos secuenciales después de un desembolso exitoso, sin duplicar la acreditación.
- Veinte rechazos simulados de pasarela, sin acreditar saldo y conservando los registros fallidos.