---
id: B-ADV-0029
title: "El bucle aplica el modelo de reserva tras agotar cuota pero conserva el arnés y la sesión del principal"
type: bug
weight: 15
dificultad: media
version: "v1.1.0"
status: completed
depende_de: []
origen: "Diagnóstico de otro agente aportado por el usuario (2026-11-07), al consultar la configuración de reservas"
created_at: 2026-11-07
updated_at: 2026-11-07
---

# B-ADV-0029: La reserva tras agotar cuota conserva el arnés y la sesión del principal

## 🎯 Descripción del Fallo

**Comportamiento reportado:** Al agotar la cuota del principal, el bucle toma el modelo de una reserva, pero los intentos quedan registrados con `arnes: codex` y con el mismo identificador de sesión de Codex. Las reservas fallan en 2–3 segundos y la tarea queda esperando aunque haya otros arneses configurados.

**Configuración descrita por el agente en el momento del fallo:** `development.dificultad.dificil` en `orchestration.json`:

- Principal: `codex`, `gpt-6.1-sol`, esfuerzo `max`.
- Reserva 1: `agy`, `gemini-4-argon`, esfuerzo `high`.
- Reserva 2: `claude`, `claude-opus-5-5`, esfuerzo `high`.

Según el agente, la configuración estaba guardada sin cambios pendientes en ese bloque. El fallo se atribuye a la aplicación de la reserva en `orquestar.py`, no a la declaración de los perfiles.

**Causa sospechada, pendiente de reproducción:** Al construir o ejecutar el perfil de reserva se sustituye el modelo pero se conserva el arnés efectivo y la sesión del perfil principal. Debe comprobarse el comando realmente lanzado para distinguir un fallo de ejecución de un fallo de atribución en métricas.

**Comportamiento esperado:** Cada reserva se ejecuta con su propio arnés, modelo y esfuerzo efectivos. Un cambio de arnés inicia una sesión compatible con el nuevo arnés, sin reutilizar la del anterior. Las métricas reflejan el perfil realmente ejecutado y su sesión. La falta de cuota del principal permite continuar con las reservas disponibles en el orden configurado.

## 📋 Reproducir

1. En un entorno de prueba aislado, configurar un perfil difícil con el principal Codex y las reservas agy y Claude descritas arriba; cubrir tanto el alias `development` como el rol `artemisa` vigente.
2. Iniciar un paso con una sesión de Codex y simular que el principal pierde cuota.
3. Capturar los comandos y argumentos de lanzamiento, las sesiones y las métricas al pasar a agy; simular después falta de cuota en agy para alcanzar Claude.
4. Comprobar que agy recibe `gemini-4-argon` y esfuerzo `high`, y Claude recibe `claude-opus-5-5` y esfuerzo `high`, cada uno con su arnés y sin la sesión de Codex.
5. Verificar que una reserva disponible puede continuar el paso y que los intentos no se atribuyen a Codex.

## 📋 Evidencias y límites

- Fuente: mensaje de otro agente copiado por el usuario el 2026-11-07. El agente afirma haber observado modelos `gemini-4-argon` y `claude-opus-5-5` registrados con `arnes: codex`, el mismo ID de sesión del principal y duraciones de 2–3 segundos.
- No se han aportado las líneas originales de métricas, el identificador de sesión ni el comando lanzado. El diagnóstico queda registrado como reporte, sin dar por confirmada la causa raíz.
- Al registrar esta incidencia, el fichero local usa `artemisa` y perfiles distintos de los descritos en el mensaje. La configuración reportada es contexto histórico para reproducir; no se modifica `orchestration.json`.
- Área a investigar: `skills/orquestar/orquestar.py`, resolución de perfiles y reservas, ejecución tras falta de cuota, traspaso de sesión y registro de métricas.
- Relacionados: B-ADV-0005 (arnés ausente), B-ADV-0011 (fallos operacionales del arnés) y B-ADV-0020 (marcas de cuota supuestas). Sus descripciones no cubren específicamente esta mezcla de arnés, modelo y sesión tras pérdida de cuota.

## Triaje y decisión de alcance

- `base_calidad`: `c90805552088882cd2c60ecf0c2018a7e8b29225`.
- Prioridad 15 (prioritario, intervalo solicitado 10–100). Versión de desarrollo v1.1.0; v1.0.0 ya está etiquetada. Los cambios ajenos existentes se conservan fuera del commit del bug.
- Causa localizada: `arnes(a, rol)` antepone `a.harness` también en cada reserva. El bucle compara ese arnés forzado para decidir la continuidad de sesión, y registra el modelo configurado aunque haya lanzado otro arnés.
- Decisión de producto aplicada a la petición de corregir las reservas: `--harness` selecciona el principal de cada paso; las reservas explícitas conservan su propio arnés. Sustituye la lectura anterior de «fuerza ese arnés en todos los pasos» en `skills/orquestar/SKILL.md:27` cuando se interpretaba también sobre las reservas. La selección del principal sigue aplicándose a todos los pasos.
- Si el arnés forzado difiere del principal configurado, no se trasladan su modelo ni su esfuerzo incompatibles. Las reservas heredan solo los campos efectivos no redefinidos. `--cmd` conserva su semántica de plantilla explícita.
- Subfase A [EXEC]: escenarios de reservas con `--harness`, herencia, sesiones y métricas; sin eliminar escenarios existentes.
- Subfase B [EXEC]: resolución de perfil efectivo una vez por paso y mapa de impacto.
- Subfase C1 [EXEC]: regresión con bucle, constructor de comandos y registro reales; arneses simulados sin red, gateway ni esperas reales.
- Subfase C2 [EXEC]: aplicación coherente del perfil a ejecución, selección de cuota, sesiones y métricas.
- Subfase D [EXEC]: revisiones independientes Hades de especificación, pruebas y código.
- Subfase E [EXEC]: manual de orquestación, skill distribuida y changelog.
- Subfase F [EXEC]: cierre y commit exclusivo del delta del bug.
- Verificación: regresión nueva, `tests.test_orquestar` y módulos `test_fallos_arnes`, `test_arnes_ausente`, `test_cuota_vigente`, `test_cuota_supuesta`; compilación, `git diff --check` y calidad del delta. Sin suite completa.

## Cierre de corrección · 2026-11-07

- Reproducción confirmada con `--harness codex`: antes del arreglo las reservas agy y Claude se lanzaban como Codex; sin override no se reproduce. Evidencia roja en `docs/review/test_reviews/B-ADV-0029-red.md`.
- Resuelto el principal efectivo una vez por paso. Las reservas conservan arnés/modelo/esfuerzo, las sesiones solo continúan dentro del mismo arnés y las cuotas y métricas usan los pares ejecutados. No se cambia `orchestration.json`.
- Hades: especificación 9/10, pruebas 9/10 y código 8,83/10, aprobados. D1 documental resuelto, sin hallazgos pendientes.
- Verificación mediante motor local y `--verificar`: **127 pruebas OK** (82 integración, 3 regresión nueva con subcasos, 14 fallos del arnés, 9 arnés ausente, 8 cuota vigente y 11 cuota supuesta). Compilación de los tres Python modificados y `git diff --check` verdes. Formato y lint omitidos por ausencia de herramientas configuradas/deducibles, según `--calidad --base c90805552088882cd2c60ecf0c2018a7e8b29225 --aplicar`; no equivalen a herramientas ejecutadas. No cambian dependencias.
- El test de cuotas vigente conserva sus cuatro casos y añade el par efectivo agotado; se actualiza la expectativa que atribuía un modelo incompatible al principal forzado. La copia de argumentos conserva atributos de clase usados por la integración.
- Versión v1.1.0 confirmada expresamente por el usuario. Corrección en `release/v1.1`; instalación global y publicación pendientes del lanzamiento de la versión.
