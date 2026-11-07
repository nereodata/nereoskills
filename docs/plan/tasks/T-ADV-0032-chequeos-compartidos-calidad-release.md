---
id: T-ADV-0032
title: "Centralizar la planificación, ejecución y reutilización de chequeos de calidad y release"
type: funcional
weight: 100
dificultad: dificil
version: "v1.1.0"
status: planned
depende_de: []
origen: "Petición del usuario (2026-11-02): suites de cierre duplicadas en Afinn y verdes antiguos que ocultan fallos posteriores"
created_at: 2026-11-02
updated_at: 2026-11-02
---

# T-ADV-0032: Centralizar la planificación, ejecución y reutilización de chequeos de calidad y release

## 🎯 Objetivo de Negocio

Adevv decide qué comprobaciones necesita un proyecto, cuáles tienen evidencia vigente, cuáles están en marcha y cuáles requieren reparación. CLI, gateway, agentes y release comparten ese servicio y su estado, evitando repetir suites costosas y acreditar resultados obsoletos.

En Afinn, un lanzador de cierre ejecutaba directamente una suite de aproximadamente una hora mientras el orquestador utilizaba su propio verificador. Esto provocó repeticiones sobre el mismo árbol. Además, el verificador actual admite cualquier verde anterior aunque haya un fallo posterior de la misma comprobación.

## Base existente y delta

Revisar y consolidar antes de extender:

- `skills/orquestar/orquestar.py`: `suite`, `arbol`, `verificar`, evidencia en `orquestar_evidencias.jsonl`, métricas, información de verificaciones en los prompts y recuperación de suite roja. Hoy la reutilización busca cualquier resultado satisfactorio por comando y árbol; la salida capturada se publica al terminar.
- `skills/orquestar/calidad.py`: resolución de formato/lint y validación del delta; contratos de T-ADV-0022.
- `skills/telegram_gateway/cierre_version.py`: precondiciones, preflight ejecutado directamente en el árbol preparado para publicar, cierre y publicación desde Telegram.
- `adevv/cli.py`, `adevv/release_tools.py`, `skills/release/` y gestión de procesos/PID: entradas y restricciones que deben converger, sin confundir la exclusión del bucle con la coordinación de todas las comprobaciones.
- T-ADV-0006 (triaje y evidencia), T-ADV-0022 (calidad del delta), T-ADV-0023 (cierre por Telegram) y B-ADV-0006 (reparación de suite roja) ya están entregadas: son antecedentes, no dependencias pendientes.

El delta es unificar planificación, ejecución, acreditación y seguimiento, con identidad suficiente y coordinación compartida. No crear un segundo orquestador ni scripts de cierre especiales por proyecto. No se ha inspeccionado aquí el repositorio de Afinn: su configuración, lanzadores y restricciones reales se comprobarán durante la migración.

## 📋 Criterios de Aceptación (Nivel Máster)

- [ ] **CA-M-1 — Registro y cobertura honesta:** cada proyecto declara sus comprobaciones de formato, lint, tipado, seguridad, secretos, dependencias, pruebas, builds y puertas de release. Se distinguen configurado, ausente, omitido con justificación, ejecutando, aprobado y fallido, conservando la diferencia entre disponibilidad y resultado. La ausencia de un análisis nunca acredita su cobertura; si es obligatorio, impide superar la puerta correspondiente. La configuración inválida se comunica como error.
- [ ] **CA-M-2 — Plan explicable:** antes de ejecutar se muestra el plan, con alcance, comandos reales y motivos de ejecución, reutilización, espera u omisión. Los cambios del plan durante diagnóstico o reparación también se explican antes de ejecutar. No se inventan comandos ni se supone cobertura por el nombre de una suite. Se conservan las deducciones existentes solo cuando están respaldadas por configuración reconocida y se muestra su origen.
- [ ] **CA-M-3 — Evidencia aplicable:** la identidad combina comando efectivo, contenido y entorno relevante, incluidas herramientas, configuración, dependencias y plataforma. Incluye cambios sin confirmar y archivos relevantes no rastreados. El SHA de commit por sí solo nunca basta. Si no puede acreditarse una entrada relevante, no se reutiliza. Un cambio durante la ejecución impide atribuir el resultado a otro contenido o entorno sin justificación verificable.
- [ ] **CA-M-4 — Coordinación por proyecto:** existe un único proceso de cierre por proyecto; solicitudes simultáneas desde cualquier entrada se unen al existente y consultan su estado. Las comprobaciones equivalentes en curso se comparten y no duplican suites. Una solicitud con otro contenido, entorno o alcance no recibe indebidamente el resultado en curso como válido; su espera y siguiente acción son visibles. La coordinación contempla worktrees y recuperación tras interrupciones sin falsos aprobados ni procesos duplicados.
- [ ] **CA-M-5 — Último resultado e intermitencias:** prevalece el último resultado aplicable de una ejecución real. Un fallo posterior invalida la acreditación de un verde anterior para esa identidad, también en los prompts de los agentes y en release. Reutilizar o consultar evidencia no crea una ejecución nueva ni altera su precedencia. Se registra el historial de intermitencias; un verde posterior no lo borra ni desencadena reintentos hasta conseguir verde como estrategia de resolución.
- [ ] **CA-M-6 — Diagnóstico y reparación:** un fallo activa el ciclo existente de diagnóstico y reparación sobre los casos afectados. Tras corregir se amplía la validación según el impacto justificado, hasta satisfacer las puertas aplicables. No se repite automáticamente todo en cada paso. Se conserva el diagnóstico, la acción siguiente y, cuando no pueda continuar autónomamente, el motivo concreto de intervención humana.
- [ ] **CA-M-7 — Caché por comprobación:** una puerta fallida no obliga a repetir las anteriores cuya evidencia siga siendo válida. Los alcances de invalidación son conservadores y configurables; una dependencia desconocida no se asume independiente. La suite global se ejecuta cuando las puertas o el impacto lo exijan, con motivo explícito.
- [ ] **CA-M-8 — Estado durante la ejecución:** todas las entradas consultan fase, comando activo, progreso disponible, evidencias, motivo de espera y siguiente acción. Hay registros consultables mientras corre el comando y tras una interrupción; no se inventa un porcentaje cuando la herramienta no lo proporciona.
- [ ] **CA-M-9 — Restricciones comunes:** validar, cerrar localmente, etiquetar y publicar son acciones distintas y respetan las restricciones y autorizaciones del proyecto. Pedir validación o disponer de un verde no autoriza por sí mismo las demás acciones. Gateway y demás entradas no pueden eludirlas. La evidencia de release corresponde al contenido realmente preparado para la operación, incluidos los cambios de integración que afecten a su validez.
- [ ] **CA-M-10 — Compatibilidad y adopción:** se mantienen las configuraciones e invocaciones actuales (`validation.command`, formato/lint, `--test`, `--verificar`, calidad del delta y `release.preflight`, con sus opciones aplicables), mediante adaptación al servicio común o transición documentada sin duplicar ejecuciones. La evidencia antigua solo se reutiliza si satisface el nuevo contrato; en otro caso se conserva como historial sin acreditar cobertura. Afinn migra al flujo común retirando las ejecuciones directas redundantes y conserva sus restricciones de release.

## Criterios BDD que desarrollar y automatizar

Estos escenarios fijan resultados observables; la especificación detallada y los casos adicionales se derivarán del diseño y del riesgo.

| Dado | Cuando | Entonces |
| --- | --- | --- |
| Un proyecto con análisis configurados y otros ausentes | Solicita validación | Ve el plan antes de ejecutar, comandos respaldados por configuración y ausencias u omisiones justificadas, sin cobertura ficticia. |
| Evidencia aprobada con entradas relevantes iguales | Otra entrada solicita esa comprobación | Reutiliza la misma evidencia sin lanzar el comando, aunque cambie el commit sin afectar las entradas relevantes. |
| Un mismo commit con contenido pendiente, herramienta, configuración, dependencia o plataforma relevante diferente | Solicita reutilizar evidencia | La comprobación afectada se invalida y el plan explica el motivo. |
| Un cierre en curso | CLI, gateway y agente solicitan simultáneamente el mismo cierre | Comparten proceso, ejecución y estado; el contador de invocaciones de la suite es uno. |
| Una comprobación en curso | Cambian entradas relevantes o llega una solicitud distinta | No acredita el nuevo estado con el resultado anterior y muestra cómo continuará. |
| Un verde seguido de un fallo aplicable de la misma comprobación | Se consulta o solicita el cierre desde cualquier entrada | Prevalece el fallo, también en el contexto entregado al agente; no se rescata el verde antiguo. |
| Resultados alternos de una misma comprobación | Aparece un verde posterior | Conserva la intermitencia y su diagnóstico; no la considera resuelta solo por ese verde. |
| Varias comprobaciones aprobadas y una puerta fallida | Se repara el fallo | Valida primero lo afectado y amplía según impacto; conserva aprobados independientes y justifica las invalidaciones. |
| Un comando largo en ejecución o un proceso interrumpido | Se consulta el estado | Hay registros parciales y estado real; la recuperación no duplica un comando todavía vivo ni inventa un aprobado. |
| Un proyecto que permite cierre local y restringe etiqueta/publicación | Se pide cerrar desde el gateway | Respeta esa separación y no etiqueta ni publica sin autorización aplicable. |
| Configuración anterior y el lanzador redundante de Afinn | Se adopta el flujo común | Mantiene los chequeos y restricciones declarados y evita la doble suite, con evidencia de la migración. |

## Entregables de desarrollo

- BDD detallado trazable a los criterios anteriores y diseño que explique qué mecanismos se consolidan, identidad/vigencia de evidencia, coordinación, invalidación, recuperación y compatibilidad.
- Pruebas de concurrencia real entre procesos/entradas, carreras de evidencia y recuperación; pruebas de caché por contenido/entorno/alcance y de fallos, intermitencias y reparación. Usar ejecutores controlados para demostrar que no se duplica una suite sin tener que repetir una suite de una hora.
- Pruebas de regresión de configuraciones y entradas actuales, restricciones de release y validación del contenido preparado para publicar.
- Migración comprobada de Afinn y documentación de configuración, operación y transición de evidencia. Si no se dispone del proyecto o de un acceso necesario, registrar el bloqueo de esa entrega y no declarar migración realizada.

## Margen de decisión y límites

Fijar garantías, no una receta: el agente decide estructura, almacenamiento, coordinación, adaptadores y selección de pruebas según lo existente y el impacto, justificando las decisiones relevantes. No se prescriben herramientas concretas, número fijo de reintentos, orden universal de chequeos ni suite completa en cada reparación. Mantener las instrucciones a agentes breves; el servicio aporta el plan y la evidencia para decidir.

No desarrollar analizadores de seguridad propios: integrar analizadores adecuados mediante adaptadores. Esta tarea registra una capacidad única de calidad y cierre compartidos; no añade herramientas de seguridad ni un orquestador paralelo.
