# Revisión de código: T-ADV-0030

- **Revisor:** Hades. **Fecha:** 2026-10-27. **Modo:** orquestado. **Ronda:** 3.
- **Artefacto:** exclusivamente el delta de producción de `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`, con lectura de sus consumidores inmediatos como contexto.
- **Contrato:** `docs/design/T-ADV-0030-design.md`, CA-M-1..4, DEC-ESP-01..04 y triaje de la tarea; reglas de capas y DEC-P03/P09 del plan de plataforma.
- **Límite:** no se revisan las pruebas, ya aprobadas. Las modificaciones documentales de las dos skills se consultan únicamente para comprobar que explican el comportamiento de producción.

## Veredicto: APROBADO

Media **9,17/10**, sin hallazgos vigentes. H-01 resuelto; no quedan pendientes para el desarrollador en esta revisión de producción.

## Análisis estático

Se reutiliza la evidencia verde del árbol `ab73346044161d850d701ee92bf49c4b3b09aef8`, registrada en `orquestar_evidencias.jsonl` y aportada por el invocante:

- `python -m unittest tests.test_orquestar tests.test_telegram_gateway skills.telegram_gateway.test_gateway_fondo`: 116 pruebas OK según el invocante.
- `python -m py_compile skills/orquestar/orquestar.py skills/telegram_gateway/gateway.py skills/telegram_gateway/test_gateway_fondo.py && git diff --check`: OK.

No se relanzan comandos. No se aportan ni se atribuyen resultados de herramientas adicionales de lint, tipado o escaneo de secretos. La inspección del delta no identifica credenciales incrustadas, construcción de comandos mediante shell ni dependencias nuevas; auditoría de dependencias no aplicable. No se requiere experimentar para resolver las cuestiones observadas por lectura.

## Puntuaciones

| Criterio | Nota | Evaluación |
|---|---:|---|
| Corrección | 9 | Precedencia independiente, origen efectivo y prohibición de escucha correctos. El diagnóstico de incompletas precede ahora a la restricción ambiental. |
| Seguridad | 10 | El rechazo precede reserva, recarga de escucha y creación de procesos en las tres entradas. No se imprimen tokens ni se introducen comandos de shell. |
| Conformidad | 9 | Objeto compatible con desempaquetado, resolución centralizada, aviso compartido y deduplicación por ejecución acordes al diseño y al plan. Se conserva el diagnóstico requerido por DEC-ESP-01. |
| Calidad | 9 | Cambio pequeño y localizado; nombres claros, motivo compartido y manejo tolerante del fallo de autoarranque conservado. |
| Eficiencia | 9 | Lecturas locales acotadas y deduplicación en memoria; sin nueva red ni persistencia. Hay una segunda resolución local de credenciales en autoarranque, de coste reducido en este flujo. |
| Documentación | 9 | Ambas skills explican precedencia, respaldo saliente y requisito de token local para escuchar. El docstring de credenciales documenta ahora las credenciales efectivas y el origen del token; se conserva el diagnóstico de incompletas. |
| **Media** | **9,17** | |

## Evaluación del delta

`CredencialesTelegram` devuelve token, usuarios y origen y conserva el desempaquetado histórico de dos valores mediante `__iter__`. Los consumidores de producción de ambos módulos usan ese contrato. La selección aplica normalización antes del respaldo, de forma que un token local vacío o de espacios no autoriza escucha. Token e IDs se seleccionan por separado; los IDs ambientales no convierten un token local en ambiental y los IDs locales no autorizan a escuchar con un token ambiental.

`telegram()` conserva los dos orígenes para avisos y sigue desactivándose sin token, sin usuarios o con telegram false. El flujo de `avisar()` mantiene prefijo de proyecto, firma y selección de eventos. No se incorpora envío ni escucha nuevos en la resolución de credenciales.

`iniciar_gateway()` consulta primero si Telegram está habilitado y las credenciales son completas. Si el token procede del entorno, termina antes del lanzador y emite el motivo una vez por raíz. `bucle()` elimina esa marca al comenzar otra ejecución. El padre de segundo plano usa informar false y deja que el hijo informe en la salida del bucle; con token local conserva el lanzamiento habitual. No hay persistencia entre procesos.

`gateway.main()` deja consultas y parada antes de la nueva política. Los modos primer plano, fondo y gestionado comparten el rechazo ambiental antes de reservar PID, lanzar hijos o alcanzar escucha. El resto del flujo de PID y recarga queda fuera del delta y no se reaudita. La política se implementa en los motores existentes, sin nueva capa, dependencia o almacenamiento, conforme a DEC-P09 y al diseño.

## Reevaluación de H-01

**Estado: resuelto.** Ubicación: `skills/telegram_gateway/gateway.py:488`.

La comprobación `if not token or not autorizados` se ejecuta antes de comprobar origen entorno. Con token ambiental presente y usuarios vacíos, termina con el mensaje histórico completo: «Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_ALLOWED_USER_IDS (en .env o en el entorno).». Con credenciales completas y token ambiental, termina con el motivo compartido de solo avisos. Ambas salidas siguen antes de `en_fondo`, `recibir_recarga`, `reservar` y `escuchar`, para los tres modos de escucha.

La corrección cumple DEC-ESP-01 sin debilitar DEC-ESP-03 ni cambiar consultas y parada. No altera la resolución de fuentes, la compatibilidad del objeto de credenciales, los avisos ni la deduplicación del bucle. En esta ronda se confirma además el docstring actualizado de `credenciales()`: describe las credenciales efectivas y el origen del token devueltos. La lógica de orquestar coincide con la ya revisada; el cambio documental es conforme al objeto previsto en el diseño. No requiere ampliar el análisis a otros módulos o arquitectura. No se identifican hallazgos nuevos.

## Alcance y cierre

El juicio se limita a producción. Se revisan el informe anterior, el diff actual de ambos módulos, el orden de las ramas y la documentación del origen; se conserva el análisis previo de diseño, CA/DEC y plan de plataforma para el resto del delta. La evidencia verde acredita las comprobaciones dirigidas indicadas, sin convertirla en una garantía de todos los casos de entrada. No se reabre la revisión de pruebas ni se juzga su cobertura.

Se actualiza únicamente este informe con el ID maestro. No se modifica código, no se ejecutan verificaciones ni se crea commit.
