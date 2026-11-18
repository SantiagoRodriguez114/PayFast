# Módulo de aportes y financiación — PayFast

## 1. Objetivo

Permitir que un prestamista aporte fondos simulados a una solicitud de crédito elegible, descontando el monto de su billetera y actualizando la financiación acumulada de la solicitud.

Este módulo implementa la funcionalidad de aportes asociada a HU-07.

## 2. Componentes principales

| Archivo | Responsabilidad |
|---|---|
| `backend/app/api/credit_requests.py` | Endpoint HTTP para registrar aportes |
| `backend/app/services/aporte_service.py` | Validaciones y operación de financiación |
| `backend/app/models/aporte.py` | Persistencia de cada aporte |
| `backend/app/models/credit_request.py` | Monto solicitado, monto financiado y estado |
| `backend/app/models/wallet.py` | Saldo disponible del prestamista |
| `backend/app/domain/states.py` | Estados permitidos de las solicitudes |
| `backend/app/schemas/aporte.py` | Validación y representación de datos |

## 3. Endpoint

`POST /credit-requests/{solicitud_id}/contributions`

La operación requiere autenticación y autorización como prestamista.

El cuerpo contiene el monto del aporte:

```json
{
  "monto": "100000.00"
}
```

El monto se representa mediante `Decimal` para evitar errores de precisión asociados a los números de punto flotante.

## 4. Reglas de negocio

Una solicitud solamente puede recibir aportes cuando se encuentra en `EVALUADA` o `EN_FINANCIACION`.

El aporte debe ser positivo, finito y no tener más de dos decimales.

El monto aportado no puede superar el saldo pendiente de financiación:

**Saldo pendiente = Monto solicitado − Monto financiado**

El prestamista debe contar con una billetera principal activa y con saldo suficiente.

Cuando el aporte se registra correctamente:

- Se descuenta el monto de la billetera del prestamista.
- Se incrementa el monto financiado de la solicitud.
- Se registra el aporte con su prestamista y solicitud asociados.
- Se actualiza el estado de la solicitud.

Si la financiación acumulada es inferior al monto solicitado, el estado será `EN_FINANCIACION`.

Si la financiación acumulada alcanza exactamente el monto solicitado, el estado será `FINANCIADA`.

## 5. Consistencia transaccional

El servicio ejecuta las operaciones dentro de una transacción de base de datos.

Primero obtiene la solicitud con `SELECT ... FOR UPDATE` y después bloquea la billetera principal del prestamista.

Estos bloqueos permiten serializar operaciones concurrentes sobre las mismas filas cuando se utiliza PostgreSQL.

La actualización del saldo, el monto financiado, el estado y el registro del aporte se confirman mediante un único `commit()`.

Si ocurre un error antes de confirmar la operación, se ejecuta `rollback()`.

Esto evita que una operación fallida deje parcialmente actualizados los saldos y el registro del aporte.

## 6. Validaciones y errores

El servicio rechaza las operaciones cuando:

- El monto no es válido.
- La solicitud no existe.
- La solicitud no admite financiación.
- El aporte supera el saldo pendiente.
- El prestamista no tiene una billetera principal activa.
- El prestamista no dispone de fondos suficientes.

Las excepciones de negocio se representan mediante `AporteError` y son traducidas por la capa API a respuestas HTTP.

## 7. Pruebas

Archivo principal: `tests/test_aporte_api.py`.

Los escenarios incluyen el registro de un aporte válido, el rechazo de aportes superiores al saldo pendiente y la financiación completa mediante un único aporte.

La prueba de financiación completa verifica el estado final de la solicitud, el monto financiado y el saldo restante del prestamista.