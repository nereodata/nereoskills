---
id: T-ADV-0023
title: "Cerrar la versión y relanzar el bucle desde Telegram"
type: funcional
weight: 100
dificultad: dificil
version: "v1.0.0"
status: completed
depende_de: []
origen: "La única intervención humana por versión obliga a volver a la máquina para lanzar /release y relanzar"
created_at: 2026-10-26
updated_at: 2026-10-27
---

# T-ADV-0023: Cerrar la versión y relanzar el bucle desde Telegram

## 🎯 Objetivo de Negocio
Cuando el bucle para con «Versión vX.Y terminada», el humano revisa y cierra con `/release`. Hoy eso exige estar en la máquina. Esta tarea permite hacer esa única intervención desde Telegram: ver el resumen de la revisión, cerrar la versión y relanzar el bucle con la siguiente.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Aviso de cierre útil):** el aviso de fin de versión por Telegram incluye un resumen de `docs/review/versions/vX.Y-revision.md` (tareas, bloqueos, validaciones funcionales pendientes) y las órdenes disponibles para cerrarla.
- [x] **CA-M-2 (Orden `/cerrar vX.Y`):** solo para usuarios autorizados y solo si el bucle está parado en la revisión de esa versión (sin bloqueos ni decisiones de producto pendientes). Ejecuta el cierre de versión de `/release` (merge a `main`, etiqueta anotada, push) en modo no interactivo y responde con el resultado. Pide confirmación explícita (p. ej. `/cerrar v1.0 confirmo`) antes de actuar.
- [x] **CA-M-3 (Relanzar):** tras un cierre correcto, relanza el bucle en segundo plano (como `/lanzar`) para que abra la siguiente versión pendiente; si no hay más, informa de `FIN`.
- [x] **CA-M-4 (Errores):** cualquier fallo (árbol sucio, conflicto de merge, push rechazado, validación de versión) no deja el repositorio a medias: se informa por Telegram con el motivo y el bucle sigue parado.
- [x] **CA-M-5 (Pruebas y documentación):** pruebas con repositorio git temporal y remoto `bare` local, sin red; documentación en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md` («Revisión de versión»).

## Triaje de desarrollo · Artemisa · modo orquestado

- **A · Definición [EXEC]**: escenarios nuevos de cierre en el feature existente del gateway; revisión aislada de Hades.
- **B · Diseño [EXEC]**: validación de precondiciones, publicación conjunta de rama y etiqueta y recuperación ante fallos.
- **C1 · Pruebas [EXEC]**: `skills/telegram_gateway/test_cierre_version.py`, con repositorios temporales y remoto bare local, credenciales ficticias, sin transporte Telegram ni procesos reales.
- **C2 · Implementación [EXEC]**: aviso resumido, comando confirmado, cierre no interactivo y relanzamiento condicionado al éxito.
- **D · QA [EXEC]**: Hades sobre el delta completo.
- **E · Documentación [EXEC]**: comandos y revisión de versión en ambas skills.
- **F · Cierre [EXEC]**: entrada de revisión de versión, tarea completed y commit semántico.
- **Verificación al cierre**: `python -m unittest skills.telegram_gateway.test_cierre_version tests.test_telegram_gateway tests.test_orquestar`; cubre el cierre y las regresiones de comandos, avisos y selección de estado. Además compilación de módulos afectados y `git diff --check`, siempre con `adevv orquestar --verificar`. No ejecutar la suite completa.

### Decisiones sin preguntar

- Reanudación Artemisa: A conserva exactamente los escenarios aprobados, sin delta que requiera otra revisión de especificación. Diseño en `docs/design/T-ADV-0023-design.md`. Se retoman los metadatos modificados por el bucle; no se fusiona el WIP completo.

- DEC-T23-01: `/cerrar vX.Y` muestra el resumen y solicita la orden literal `/cerrar vX.Y confirmo`; la confirmación expresa en el mismo mensaje basta, no se mantiene una sesión de confirmación.
- DEC-T23-02: cierre solo en la rama release exacta y estado PARAR de revisión final, con todos los ítems de la versión completed/cancelled y sin decisiones de producto pendientes. Se rechaza un PID de bucle existente de forma conservadora.
- DEC-T23-03: publicar main y la etiqueta anotada mediante push atómico; si el servidor no lo admite se rechaza sin publicar parcialmente. No se fuerza ni sobrescribe ninguna etiqueta existente.
- DEC-T23-04: un fallo de relanzamiento posterior a publicación se informa como versión cerrada con relanzamiento pendiente; no se deshace una versión publicada. CI/post-tag queda para revisión humana, sin esperar servicios externos.


### Resolución del especificador · 2026-10-27

- H-01: los escenarios fijan la base elegible completa y rechazan por separado tareas planned, in_progress y parada por petición manual sin PID. El camino permitido incluye una tarea cancelled.
- H-02: cada fila varía un único impedimento y fija remitente y motivo observable; no se admite un rechazo incidental como evidencia.
- DEC-ESP-01: conservar DEC-T23-01..04 del borrador, con sus límites explícitos. Se descartan confirmaciones persistentes (el mensaje literal basta), cierre por mera ausencia de PID (no acredita revisión final), push separado o forzado (admite publicación parcial o sobrescritura) y revertir una publicación por fallo de arranque (ya es visible en remoto).
- DEC-ESP-02: el estado elegible exige ítems de v1.0.0 completed/cancelled, revisión de arquitectura presente, producto ausente o APLICADA, rama release/v1.0, ningún PID del bucle y PARAR por revisión final. Se descarta interpretar una parada manual o por error como autorización de cierre. Las tareas de v1.1.0 no bloquean el cierre de v1.0.0.
- DEC-ESP-03: corregir el borrador recuperando únicamente escenarios y decisiones del WIP; se descarta fusionar la rama entera. Los escenarios anteriores del árbol actual permanecen íntegros. No se implementa producción ni tests en este paso.
- Verificación de este paso: únicamente `adevv orquestar --verificar "git diff --check"` (triaje documental A). La automatización, rojo y pruebas del triaje de desarrollo siguen pendientes; no se atribuye evidencia funcional al borrador ni se pasa suite completa.

- Revisión aislada vigente: Hades APROBADO, media 9/10, H-01/H-02 resueltos y sin hallazgos pendientes; `docs/review/spec_reviews/T-ADV-0023-spec-review.md`.
- Interrupción: el lanzador ordenó terminar sin cambiar estados por el contador de rechazos acumulados, después de emitir el veredicto aprobatorio. Se guarda este avance y se mantienen blocked/pendiente_de: especificador; el paso no se marca completado. No hay requisito externo ni pregunta humana pendiente.

### Reanudación del especificador · 2026-10-27

- DEC-ESP-04: conservar la especificación y la aprobación vigente de Hades sin repetir `/review-spec`, pues no hay delta respecto a los escenarios aprobados en `c8ca47d`. Se descartan reescribir escenarios correctos o repetir la revisión solo por la interrupción del lanzador: no queda ningún hallazgo pendiente y la skill excluye de nueva revisión lo ya aprobado. La nueva invocación permite cerrar el paso interrumpido y devolver la tarea a `planned`, sin `pendiente_de`.
- Verificación de este paso: únicamente `adevv orquestar --verificar "git diff --check"`, según triaje documental A, sobre el árbol final antes del commit. Se reutiliza evidencia si coincide el árbol. El desarrollo, sus pruebas dirigidas y QA siguen pendientes; no se declara funcionalidad implementada ni se ejecuta la suite completa.

### Cierre de desarrollo · 2026-10-27

- Pruebas: 105 OK mediante el comando del triaje con --verificar, compilación y diff limpios. Hades aprobó pruebas (8,75/10) y código final (9/10), sin hallazgos pendientes ni deuda que registrar. Validación humana trasladada a docs/review/versions/v1.0-revision.md. No se ejecutó suite completa ni se publicó el repositorio real.
