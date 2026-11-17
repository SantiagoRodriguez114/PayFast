# Evaluación de riesgo crediticio

## Objetivo

El módulo permite evaluar las solicitudes de crédito mediante un simulador de buró de crédito. Registra los resultados de cada intento y actualiza el estado de la solicitud cuando la evaluación se completa correctamente.

La integración utiliza datos ficticios. No consulta entidades financieras ni burós reales.

## Flujo de evaluación

1. El emprendedor registra una solicitud de crédito.
2. La solicitud queda en estado `PENDIENTE_EVALUACION`.
3. El usuario solicita la evaluación.
4. El sistema consulta el buró simulado.
5. Si la consulta falla, registra una evaluación `FALLIDA` y conserva el estado de la solicitud.
6. Si la consulta tiene éxito, calcula un puntaje entre 0 y 100.
7. El sistema registra el resultado y actualiza el estado:
   - Puntaje igual o superior a 50: `EVALUADA`.
   - Puntaje inferior a 50: `RECHAZADA`.

Una solicitud que ya no está pendiente de evaluación no puede evaluarse nuevamente.

## Simulador de buró

El simulador genera datos ficticios y deterministas a partir del identificador de la solicitud. Puede simular indisponibilidad del servicio.

Los datos generados son:

- Historial de pagos.
- Nivel de endeudamiento.
- Número de moras en los últimos 12 meses.
- Antigüedad crediticia en meses.

## Cálculo del puntaje

El cálculo utiliza las siguientes ponderaciones provisionales:

| Factor | Ponderación |
|---|---:|
| Historial de pagos | 50 % |
| Nivel de endeudamiento | 30 % |
| Historial de moras | 20 % |

La antigüedad crediticia se conserva como dato informativo y no participa en el cálculo actual.

## Persistencia

Cada intento se almacena en la tabla `evaluacion_riesgo`, relacionada con `solicitud_credito`.

Se registra:

- Identificador de la evaluación.
- Solicitud asociada.
- Resultado (`EXITOSA` o `FALLIDA`).
- Puntaje, cuando existe.
- Datos recibidos del simulador.
- Detalle del error, si ocurre.
- Fecha y hora de evaluación.

Los intentos fallidos también se conservan para mantener el historial.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/credit-requests/{solicitud_id}/risk-evaluations` | Ejecutar una evaluación |
| GET | `/credit-requests/{solicitud_id}/risk-evaluations` | Consultar el historial |

Ambos endpoints requieren autenticación y verifican que la solicitud pertenezca al usuario autenticado.

## Respuestas principales

- `201 Created`: evaluación registrada, tanto exitosa como fallida.
- `401 Unauthorized`: usuario no autenticado.
- `404 Not Found`: solicitud inexistente o perteneciente a otro usuario.
- `409 Conflict`: solicitud que no está pendiente de evaluación.

## Pruebas

Las pruebas de integración verifican:

- Evaluación exitosa.
- Transición a `EVALUADA` con puntaje de 50 o superior.
- Transición a `RECHAZADA` con puntaje inferior a 50.
- Fallo del buró sin modificación del estado.
- Reintento después de un fallo.
- Rechazo de evaluaciones repetidas después de una evaluación exitosa.
- Consulta del historial.
- Autenticación y autorización por propietario.
