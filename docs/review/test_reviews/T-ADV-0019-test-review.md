# Revisión de Pruebas: T-ADV-0019

- **Tarea**: `docs/plan/tasks/T-ADV-0019-firma-version-en-telegram-y-modelos-siempre-en-estado.md`
- **Diseño de referencia**: `docs/design/T-ADV-0019-design.md`
- **Archivos revisados**: `skills/orquestar/test_firma_telegram.py`, `skills/telegram_gateway/test_firma_gateway.py`.
- **Criterios**: CA-M-1, CA-M-2 y CA-M-3; triaje C1, sin `.feature` por ser lógica interna conforme a DEC-P10.
- **Ronda vigente**: **Ronda 2 — reevaluación de H1, H2 y H3** (2026-10-24).
- **Veredicto vigente**: **APROBADO**.
- **Puntuación media vigente**: **8.75 / 10**. Sin hallazgos críticos ni altos pendientes.

## Historial: Ronda 1

Veredicto: **RECHAZADO**. Media: **7.25 / 10**. Los hallazgos siguientes describen el estado anterior; su resolución consta en la Ronda 2.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Cobertura | 6 | Cubren formato básico y conversacional, idempotencia positiva, avisar(), enviar(), ocho comandos y errores en escuchar(). Faltan /agentes, resolución aislada de las fuentes alternativas de versión y discriminación entre firma final y texto intermedio. |
| Aserciones | 8 | Las igualdades de formato y del texto enviado a la API discriminan cambios reales; avisar() comprueba también contenido y destinatario. La conversación solo exige el sufijo, y el control de duplicados en escuchar() solo excluye una secuencia literal concreta. |
| Rojo correcto | 9 | La evidencia entregada atribuye el rojo a funciones nuevas ausentes y firmas ausentes, coherente con la funcionalidad pendiente y con py_compile limpio. El bucle de comandos no acredita el rojo individual de todos sus elementos porque se interrumpe en el primer fallo. |
| Estabilidad | 6 | Los temporales y mocks de red, configuración e invocación aíslan buena parte del comportamiento. Sin embargo, la versión real del paquete, la ruta del módulo y el manifiesto no se aíslan, aunque casi todas las expectativas fijan 0.5.0. |

## Hallazgos

### H1 — 🟠 ALTA: La versión del proceso no queda comprobada con fuentes controladas

- **Ubicación**: `skills/orquestar/test_firma_telegram.py:13`, `:24`, `:30`; expectativas de versión en ambos módulos.
- **Criterio**: CA-M-1; detección jerárquica de versión del diseño, sección 1.
- **Evidencia e impacto**: El único origen construido expresamente es una ruta de almacén con ADEVV_HOME temporal y versión 0.6.2. `test_version_adevv_desde_paquete_o_pyproject` llama sin preparar paquete, manifiesto ni ausencias y espera 0.5.0: pasaría devolviendo siempre el valor por defecto fuera del almacén. No discrimina paquete frente a manifiesto ni su precedencia. Además, las pruebas de formato e integración dependen de que el entorno real resuelva exactamente 0.5.0; una instalación o versión del repositorio diferente puede hacerlas fallar sin regresión funcional.
- **Corrección requerida**: Separar casos de resolución con fuentes controladas y versiones distintas: paquete, manifiesto sin paquete y ausencia de ambos, comprobando la prioridad cuando coexistan. Aislar también la fuente de versión en las pruebas de formato e integración, sin sustituir firmar() ni la integración que se pretende verificar. Mantener la prueba real de resolución por ruta.
- **Destino**: `resolver`.
- **Para**: `desarrollador`.

### H2 — 🟡 MEDIA: Falta /agentes y el rojo de comandos se detiene en /estado

- **Ubicación**: `skills/telegram_gateway/test_firma_gateway.py:21`, `:30`, `:40`.
- **Criterio**: CA-M-1 y CA-M-3.
- **Evidencia e impacto**: La lista omite /agentes, incluido expresamente en el requisito y el diseño. El for no usa subTest ni pruebas separadas: una firma ausente en /estado impide ejecutar las comprobaciones de /parar, /lanzar, /metricas, /tarea, /bug, /nuevo y /ayuda en esa ejecución. El resumen agregado del rojo no demuestra que hayan fallado individualmente.
- **Corrección requerida**: Añadir /agentes con su preparación aislada y ejecutar cada comando como subTest o prueba independiente para obtener evidencia de todos incluso si falla el primero.
- **Destino**: `resolver`.
- **Para**: `desarrollador`.

### H3 — 🟡 MEDIA: No se distingue una firma final de una mención dentro del cuerpo

- **Ubicación**: `skills/orquestar/test_firma_telegram.py:42`, `:51`.
- **Criterio**: CA-M-1 y CA-M-2; firma al pie e idempotencia sobre firma final.
- **Evidencia e impacto**: Los casos negativos no contienen el patrón con guion que sí aparece en las firmas. Un detector que acepte una coincidencia en cualquier parte del texto superaría estas pruebas: por ejemplo, una mención «— Adevv v0.4.0» seguida de más contenido podría impedir añadir la firma del proceso al pie.
- **Corrección requerida**: Añadir un mensaje que contenga ese patrón en el cuerpo y termine en texto sin firmar; comprobar que tiene_firma() no lo considera firma final y que firmar() conserva el cuerpo y añade la firma al pie. Conservar los positivos de firma final estándar y conversacional.
- **Destino**: `resolver`.
- **Para**: `desarrollador`.

## Evidencia y alcance

Auditoría estática exclusiva de las pruebas indicadas, sus datos y mocks, contrastadas con la tarea y el diseño. No se ha inspeccionado ni evaluado el código de producción, ni se han modificado pruebas o diseño.

Se acepta como evidencia proporcionada la compilación limpia mediante `python -m py_compile` de ambos módulos y el rojo de 12 tests en 0.022 s, con 6 failures y 6 errors: ausencia inicial de version_adevv, firmar y tiene_firma, y ausencia de firma en los puntos de integración ejercitados. No se repiten estas verificaciones. La falta inicial de las funciones nuevas es un rojo válido del contrato pendiente; no se atribuye a errores de sintaxis o fixtures. No se afirma que cada comando del for haya sido ejecutado en ese rojo.


## Ronda 2 — Reevaluación

**Veredicto: APROBADO. Media: 8.75 / 10.** H1, H2 y H3 resueltos; sin hallazgos nuevos ni hallazgos críticos o altos pendientes.

### Estado de los hallazgos anteriores

| Hallazgo | Estado | Evidencia de resolución |
| :--- | :--- | :--- |
| H1 — Fuentes de versión y aislamiento | **resuelto** | `test_version_adevv_desde_almacen_versiones` construye una ruta temporal bajo `ADEVV_HOME/versions/0.6.2/`. El caso de paquete inyecta `adevv.__version__ = '0.7.0'` y un manifiesto con `0.8.0`, comprobando la precedencia. Los casos de manifiesto y defecto bloquean la importación mediante `sys.modules['adevv'] = None` y esperan respectivamente `0.8.0` y `0.5.0`. Las pruebas de formato e integración aíslan `version_adevv` con `patch.object`, sin sustituir `firmar` ni el punto de integración evaluado. |
| H2 — Comandos y rojo individual | **resuelto** | `test_comandos_incluyen_firma_de_version` incluye `/estado`, `/agentes`, `/parar`, `/lanzar`, `/metricas`, `/tarea`, `/bug`, `/nuevo` y `/ayuda`. Cada comando se ejecuta dentro de `self.subTest(cmd=cmd)`, por lo que un fallo no impide comprobar los siguientes. Los mocks de estado y detalle preparan también `/agentes`. La evidencia de rojo aportada acredita el fallo individual de los nueve comandos. |
| H3 — Mención intermedia frente a firma final | **resuelto** | `test_tiene_firma_distingue_mencion_en_cuerpo_de_firma_final` exige que una mención `— Adevv v0.4.0` seguida de más contenido no sea firma final. Comprueba por igualdad que `firmar` conserva todo el cuerpo y añade la firma al pie. Mantiene positivos de firma final estándar, conversacional y con espacios/salto final, con conservación exacta del texto y sin duplicación. |

### Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Cobertura | 9 | Se cubren las cuatro vías de resolución de versión, precedencia del paquete frente al manifiesto, formato estándar y conversacional, distinción de firma final, idempotencia, avisos, envío a la API, los nueve comandos, conversación y respuesta de error. Satisfacen el alcance C1 de CA-M-1..CA-M-3 sin `.feature`, conforme al triaje. |
| Aserciones | 8 | Las versiones esperadas distintas discriminan las fuentes; las igualdades de formato, conservación del cuerpo y texto remitido a la API verifican comportamiento real. Se conserva la limitación ya observada en la primera ronda: conversación y comandos comprueban principalmente el sufijo, y la comprobación de duplicados en `escuchar` excluye una secuencia literal concreta. La idempotencia se comprueba además por igualdad exacta en las pruebas de firma y envío. |
| Rojo correcto | 9 | La compilación limpia y la evidencia entregada de 13 tests con 13 failures y 8 errors atribuyen el rojo al contrato pendiente: funciones nuevas ausentes y firmas ausentes en las integraciones. Los nueve comandos cuentan ahora con evidencia individual mediante subtests. Los subtests explican que el número de fallos pueda superar el de métodos de prueba. |
| Estabilidad | 9 | Los temporales y mocks controlan paquete, manifiesto de prueba, versión para formato e integración, red, configuración e invocación. Las expectativas de firma dejan de depender de la versión instalada o del repositorio. No se introducen dependencias del reloj ni de servicios externos. |

### Hallazgos nuevos

Ninguno. Las correcciones no muestran regresiones relevantes en las pruebas revisadas. Las limitaciones de aserción conservadas se reflejan en la puntuación y no reabren H1, H2 ni H3.

### Evidencia y alcance de la reevaluación

Revisión estática de los dos módulos de prueba, sus fixtures y mocks, contrastados con la tarea, el diseño y el informe anterior. Se revisan las correcciones y su interacción con el resto de las pruebas de estos módulos, sin ampliar la auditoría al código de producci?n ni modificar pruebas o diseño.

Se acepta como evidencia proporcionada `python -m py_compile` limpio sobre ambos módulos y la salida actualizada del rojo: `Ran 13 tests in 0.037s`, `FAILED (failures=13, errors=8)`. Según la evidencia entregada, fallan individualmente los nueve comandos, faltan `version_adevv`, `firmar` y `tiene_firma`, y faltan firmas en `avisar`, `enviar`, `conversar` y `escuchar`. No se repiten esas verificaciones ni se presenta esta revisión como una ejecución propia o como evidencia de implementación en verde.
