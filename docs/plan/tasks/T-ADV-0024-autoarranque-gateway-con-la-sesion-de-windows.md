---
id: T-ADV-0024
title: "Arranque del gateway de Telegram con la sesión de Windows"
type: funcional
weight: 110
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
origen: "NO-01 de docs/requirements/requirements.md, aplazado a una versión posterior"
created_at: 2026-10-26
updated_at: 2026-10-27
---

# T-ADV-0024: Arranque del gateway de Telegram con la sesión de Windows

## 🎯 Objetivo de Negocio
Que los gateways de Telegram de los proyectos configurados estén siempre escuchando tras iniciar sesión, sin abrir una terminal, para poder consultar el estado, recibir avisos y cerrar versiones (T-ADV-0023) desde el móvil.

## 📋 Criterios de Aceptación (Nivel Máster)
- [x] **CA-M-1 (Orden):** `adevv telegram --autoarranque on|off|estado` en la raíz de un proyecto registra, quita o muestra el arranque de su gateway con la sesión del usuario. Usa la orden `adevv` (nunca rutas al almacén de versiones), de modo que sobrevive a las actualizaciones.
- [x] **CA-M-2 (Mecanismo en Windows):** una entrada por proyecto en el arranque de usuario (carpeta Inicio o Programador de tareas, sin privilegios de administrador) que ejecuta `adevv telegram --fondo` en ese proyecto, sin ventana visible.
- [x] **CA-M-3 (Robustez):** si el proyecto ya no existe o no tiene credenciales, el arranque no falla en bucle: registra el motivo y termina. Activarlo dos veces no duplica la entrada.
- [x] **CA-M-4 (Otros SO):** en sistemas no Windows, `on` informa de que no está soportado sin cambiar nada.
- [x] **CA-M-5 (Pruebas y documentación):** pruebas con la carpeta de arranque y el lanzador simulados; documentación en `skills/telegram_gateway/SKILL.md`.

## Resolución del especificador · 2026-10-27

- **Delta real:** el gateway ya admite `--fondo`, evita duplicados y exige token local, con IDs locales o ambientales. Falta gestionar el registro y ejecutar el arranque con la sesión de Windows: la CLI actual no admite `--autoarranque`. Historial consultado: `fab6581` (borrador rechazado en WIP) y `1ff3149` (bloqueo); no se fusiona WIP ni se recuperan implementación, tests o diseño.
- **DEC-ESP-01 (H-01):** `on`, `off` y `estado` se ejecutan desde la raíz seleccionada. Éxito devuelve cero; la salida identifica proyecto y registrado/no registrado. `off` es idempotente, elimina solo la entrada propia y conserva íntegra la ajena; `estado` no modifica entradas. Se descarta un estado genérico o exigir error al repetir la baja: impedirían verificar el resultado y dificultarían su uso repetido.
- **DEC-ESP-02 (H-02):** carpeta Inicio del usuario, sin elevación, una entrada por raíz de proyecto; al simular inicio de sesión se observa el lanzamiento efectivo de `adevv telegram --fondo` con raíz absoluta correcta y ventana oculta. Se elige Inicio frente al Programador por simplicidad y facilidad para simularlo; no se prescribe formato ni nombre de archivo. Se descarta validar solo el contenido del registro, porque no prueba su ejecución. La raíz de ejemplo contiene espacios.
- **DEC-ESP-03 (H-03):** separar proyecto eliminado, token ausente, token exclusivamente ambiental e IDs ausentes. Todos terminan sin escucha, PID ni reintentos y con diagnóstico observable de la causa; el token del entorno conserva el motivo vigente de solo avisos. Los IDs ambientales con token local sí permiten el arranque. Se descarta tratar los IDs ambientales como credenciales inválidas o agrupar todos los errores en una alternativa. No se impone ubicación nueva ni literal adicional al diagnóstico existente.
- **DEC-ESP-04:** incorporar el delta al feature funcional existente `skills/telegram_gateway/features/telegram_gateway.feature` bajo `@T-ADV-0024`, preservando todos sus escenarios previos. Se descarta crear un archivo nominal de tarea o recuperar el borrador rechazado como contrato aprobado.
- **DEC-ESP-05:** no Windows rechaza `on` con código distinto de cero y sin efectos. No se amplía el contrato multiplataforma de `off|estado`, fuera del criterio pedido. Pruebas con datos ficticios, entorno aislado/restaurado, Inicio y lanzador simulados; se descarta usar el Inicio real, credenciales reales o Telegram durante la validación.
- **Revisión vigente:** Hades `/review-spec` APROBADO, 9,25/10, H-01..H-03 resueltos y sin hallazgos nuevos; reporte en `docs/review/spec_reviews/T-ADV-0024-spec-review.md`.
- **Interrupción del cierre:** tras la aprobación, el lanzador informó de dos rechazos consecutivos y ordenó commitear y terminar sin cambiar estados, para que el bucle suba dificultad y relance. Se conserva `blocked` con `pendiente_de: especificador` por esa orden, sin hallazgo de especificación pendiente ni recurso humano necesario. No se declara completado el paso; corresponde al bucle reevaluar la aprobación vigente y reanudar el cierre.

## Reanudación y cierre del especificador · 2026-10-27

- **DEC-ESP-06:** se conserva íntegra la especificación aprobada en `ba046de` y su reporte vigente de Hades (APROBADO, 9,25/10). No hay delta de escenarios ni hallazgos pendientes; `/review-spec` excluye de nueva revisión los escenarios ya aprobados. Se descarta repetir la revisión sin cambios porque no aporta evidencia nueva.
- La nueva ejecución de `especificar` reanuda el cierre interrumpido. La orden del lanzador anterior es un antecedente de aquella ejecución, no un bloqueo vigente ni una necesidad de recurso humano. Al cierre se devuelve únicamente T-ADV-0024 a `planned` sin `pendiente_de`; el bucle decidirá el siguiente paso de desarrollo.
- No se recuperan implementación, pruebas ni diseño de WIP. Los criterios permanecen pendientes y se conserva el triaje; en este paso documental solo se verifica `git diff --check` mediante el verificador del orquestador.

## Triaje conservado y ajuste para especificar

- **A · Definición [EXEC]:** resolver H-01..H-03, nueva revisión aislada `/review-spec`; en este paso documental verificar únicamente `adevv orquestar --verificar "git diff --check"`. Sin implementación, tests nuevos ni pruebas funcionales todavía inexistentes.
- **B · Diseño [EXEC, siguiente desarrollo]:** frontera Windows y entrada de Inicio determinista y simulable, sin modificar el Inicio real.
- **C1 · Pruebas [EXEC, siguiente desarrollo]:** pruebas unitarias con plataforma, Inicio y lanzador simulados. Comando del triaje original: `python -m unittest skills.telegram_gateway.test_autoarranque_windows`.
- **C2 · Implementación [EXEC, siguiente desarrollo]:** CLI y gestión del autoarranque en `skills/telegram_gateway/`.
- **D · QA [EXEC, siguiente desarrollo]:** revisiones de Hades y evidencia reutilizable mediante `adevv orquestar --verificar` sobre el mismo árbol, solo con el comando C1. Suite completa reservada al bucle al cerrar versión.
- **E · Documentación [EXEC, siguiente desarrollo]:** actualizar `skills/telegram_gateway/SKILL.md`.
- **F · Cierre [EXEC, siguiente desarrollo]:** completar tarea y commit semántico tras desarrollar; los criterios permanecen sin marcar en especificar.

## Triaje de desarrollo · 2026-10-27

- **Base de calidad:** `5c4ffee9555a2efa5bdd2884a16073c396924f64`; dificultad media conservada del bucle.
- **A [SKIP]:** escenarios @T-ADV-0024 ya incorporados y aprobados; sin delta ni nueva review-spec.
- **B [EXEC]:** registro determinista en Inicio de usuario y ejecución oculta; diseño nuevo, sin recuperar WIP.
- **C1 [EXEC]:** `python -m unittest skills.telegram_gateway.test_autoarranque_windows`; incluye ejecución real del intérprete de Inicio de Windows contra lanzador ficticio, sin red ni Inicio real.
- **C2 [EXEC]:** CLI y generación de entrada en gateway.py, reutilizando validación y lifecycle existentes.
- **D [EXEC]:** Hades review-test y review-code sobre el alcance conjunto; evidencia con --verificar.
- **E [EXEC]:** guía telegram_gateway/SKILL.md, changelog y revisión de versión.
- **F [EXEC]:** completed y commit tras QA.
- **Verificación al cierre:** comando C1 y `git diff --check`, compilación del delta; sin herramientas de lint/tipado configuradas, sin dependencias nuevas. Suite completa reservada al bucle.
- **DEC-DEV-01:** entrada VBS mínima en Inicio de usuario (carpeta especial Windows), que ejecuta PowerShell codificado en UTF-16LE con ventana 0 y espera su salida. PowerShell fija raíz literal, comprueba existencia y llama la orden pública `adevv telegram --fondo`, conservando diagnósticos en LocalAppData/Adevv/autoarranque. No se guarda token ni ruta a una versión instalada.
