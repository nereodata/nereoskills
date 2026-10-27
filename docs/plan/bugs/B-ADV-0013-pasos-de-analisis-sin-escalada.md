---
id: B-ADV-0013
title: "Los pasos de análisis paran tras 2 intentos sin escalar de modelo ni probar reservas"
type: bug
weight: 25
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0013: Los pasos de análisis paran tras 2 intentos sin escalar de modelo ni probar reservas

## 🎯 Descripción del Fallo

**Causa raíz**: la promoción de dificultad cuando no hay progreso (`promover_dificultad()`, `comprobar_promocion()`) solo se aplica a `task-dev` y `bug-fix`. `especificar`, `revisar-tarea`, `revisar-version`, `calcular-dependencias`, `work-plan`, `revisar-deuda` y `aplicar-producto` paran con «"<paso>" no avanza tras 2 intentos».

**Comportamiento observado**: en v1.0, «"especificar" no avanza tras 2 intentos» (B-ADV-0007) detuvo el bucle sin probar un modelo más fuerte.

**Comportamiento esperado**:
1. Antes de parar, un paso de análisis sin progreso se repite con el perfil escalado del rol (`escalada()` / el siguiente nivel configurado) y después con las reservas.
2. Si sigue sin avanzar y el paso afecta a una tarea concreta (`especificar`, `revisar-tarea`), esa tarea se bloquea con `pendiente_de: humano` y el bucle continúa, como en B-ADV-0012. Si el paso es de toda la versión o de todo el producto, entonces para.
3. El aviso dice qué perfiles se probaron.
4. Pruebas con un paso de análisis simulado que solo avanza con el perfil escalado.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.

## Antecedente del bloqueo (2026-10-27)
Hades /review-spec RECHAZADO (7,5/10), con H-01/H-02 altos y H-03 medio para el especificador. Intento conservado en `wip/B-ADV-0013` (6b43e5c). Se corrige aquí el contrato sin recuperar diseño, producción ni pruebas de esa rama. El reporte vigente sustituye al rechazo histórico.

## Triaje
- Especificar, fase actual: [EXEC] contrato y escenarios de sistema en `tests/features/uso_sin_rutas.feature`; revisión aislada `/review-spec`. Verificación documental: `adevv orquestar --verificar "git diff --check"`.
- Desarrollo posterior: A [EXEC] consumir esta especificación aprobada; B [EXEC] diseño de recuperación por paso/argumento; C1 [EXEC] bucle simulado, perfiles, agotamiento, aislamiento, progreso y recarga; C2 [EXEC] motor; D [EXEC] Hades; E [EXEC] contrato operativo en `skills/orquestar/SKILL.md`; F [EXEC] cierre y commit.
- Verificación de desarrollo: `adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py"` y pruebas de recarga afectadas: `adevv orquestar --verificar "python -m unittest discover -s skills/orquestar -p test_recarga.py"`. Sin suite completa: corresponde al bucle al cerrar versión.
- El rojo de WIP (cuatro pruebas, cinco fallos en `RecuperacionAnalisisTests`) es antecedente de otro árbol, no evidencia del actual. Atenea no recupera ni escribe tests ejecutables.

## Contrato de recuperación de análisis
Aplica a `especificar`, `revisar-tarea`, `revisar-version`, `calcular-dependencias`, `work-plan`, `revisar-deuda` y `aplicar-producto` cuando el arnés termina correctamente pero no cambia la firma de progreso existente. No redefine qué constituye progreso, los fallos operacionales ni la recuperación por cuota.

Cada par `(paso, argumento)` tiene una cadena independiente: perfil inicial efectivo → niveles superiores configurados, en orden sencilla/media/dificil → escalada del rol → reservas declaradas del perfil inicial, en su orden. Las sobreescrituras por paso y la herencia de campos se resuelven antes de comparar perfiles. La identidad para deduplicar es `(harness, model, effort)` efectivo; se conserva la primera aparición. Las reservas propias de los niveles y de la escalada no expanden recursivamente esta cadena por falta de progreso. Cada perfil admite exactamente `--reintentos` ejecuciones consecutivas sin progreso; cambiar de perfil inicia sesión nueva y contador cero. Si uno avanza se termina la cadena sin probar los restantes.

### Configuración común de los ejemplos B-ADV-0013
Perfiles ficticios distinguibles para un arnés simulado, sin llamadas a proveedores; `--reintentos=2`, cuota disponible, sin fallos operacionales, árbol limpio tras cada ejecución, sin alcanzar `--max-pasos` ni petición de parada. El rol efectivo del paso declara:

| Posición configurada | harness | model | effort |
| --- | --- | --- | --- |
| Inicial y dificultad media | codex | base-demo | medium |
| Dificultad dificil | codex | superior-demo | high |
| Escalada | claude | escalado-demo | high |
| Reserva 1 del inicial | codex | superior-demo | high |
| Reserva 2 del inicial | agy | reserva-demo | medium |

Para pasos con ID, su dificultad inicial es media. Para pasos globales sin dificultad se parte del perfil inicial del rol y nivel media por defecto. No hay otras sobreescrituras. En cada escenario, «configuración común» significa exactamente esta tabla. Secuencia completa sin progreso esperada (ocho ejecuciones): `codex/base-demo/medium` ×2 → `codex/superior-demo/high` ×2 → `claude/escalado-demo/high` ×2 → `agy/reserva-demo/medium` ×2. La reserva 1 se omite porque coincide con el nivel superior; no elimina los dos intentos permitidos de ese nivel.

Agotada la cadena, solo `especificar` y `revisar-tarea` bloquean el ID: `status: blocked`, `pendiente_de: humano`, motivo en tarea y revisión de versión, aviso en consola y Telegram (simulado). Se conserva el aislamiento de B-ADV-0012: independientes elegibles continúan y dependientes esperan. Los otros cinco pasos paran con diagnóstico y sin modificar estados de tareas. Diagnóstico y aviso enumeran los cuatro perfiles efectivos anteriores en orden y sus dos intentos por perfil, el paso y su argumento.

## Decisiones sin preguntar
- **DEC-ESP-13-01:** niveles superiores → escalada → reservas del inicial, con deduplicación efectiva. Se descarta saltar directamente a reservas y expandir reservas de cada nivel: impide omisiones y fija una cadena finita, verificable. Se conserva la recuperación ya existente de `task-dev`/`bug-fix`.
- **DEC-ESP-13-02:** los niveles son perfiles de recuperación del par, sin reescribir la dificultad del backlog para estos pasos. En globales se usa media por defecto; se descarta inventar una tarea para almacenar la dificultad. Una configuración sin niveles ni escalada recorre inicial y reservas; sin alternativas, agotar el inicial basta para el desenlace local/global.
- **DEC-ESP-13-03:** cada par conserva su perfil pendiente e intentos aunque se intercale otro par sin que el primero avance. Un progreso real de un par borra solo su recuperación, de modo que si vuelve a necesitar el mismo paso arranca del inicial con todos sus intentos. Se descarta un contador global y reiniciar solo por cambiar de par, porque mezclan o pierden agotamientos.
- **DEC-ESP-13-04:** la recarga cooperativa conserva la recuperación de todos los pares, incluido el contador parcial del perfil activo; se descarta reiniciar en base o conceder intentos adicionales. No se exige persistencia entre paradas manuales independientes.
- **DEC-ESP-13-05:** fixtures de selección de pasos y arneses simulados permiten intercalar pares sin progreso artificial ni efectos externos. Se descarta ejecutar agentes reales o reutilizar como verde el rojo de WIP. H-01 se resuelve con secuencias y éxito en reserva; H-02 con aislamiento, reinicio y recarga; H-03 con esquemas locales, independiente elegible y límite explícito.

## Triaje de desarrollo (Artemisa)
- A [EXEC]: consumir especificación aprobada; sin cambios de contrato ni nueva revisión spec.
- B [EXEC]: diseño por par en docs/design/B-ADV-0013-design.md.
- C1 [EXEC]: pruebas de éxito, agotamiento, aislamiento, progreso y recarga.
- C2 [EXEC]: motor de recuperación de análisis.
- D [EXEC]: Hades sobre todo el delta.
- E [EXEC]: skill orquestar, README y changelog existente.
- F [EXEC]: cierre y commit.
- Verificación: los dos comandos unittest del triaje aprobado y `git diff --check`, todos con `--verificar`; sin herramientas de lint/tipado configuradas ni dependencias nuevas.

## Resolución

Cadena de análisis independiente por paso y argumento, con niveles superiores,
escalada y reservas originales deduplicadas. Conserva perfiles e intentos en
recarga; el progreso reinicia solo su par. El agotamiento local bloquea el ID y
continúa con independientes; el global informa de los perfiles probados y para.
Los rechazos previos de Hades no alteran esta cadena; desarrollo conserva su
escalada propia. Se sincroniza el contrato operativo y se conserva UTF-8.

Verificación con `adevv orquestar --verificar`: 80 pruebas de
`test_orquestar.py`, 11 de `test_recarga.py` y `git diff --check` en verde.
Hades: especificación aprobada; pruebas y código aprobados con 9/10, sin
hallazgos pendientes. C-01, C-02 y C-03 resueltos. Validación de versión en
`docs/review/versions/v1.0-revision.md`. No se ejecuta la suite completa.
