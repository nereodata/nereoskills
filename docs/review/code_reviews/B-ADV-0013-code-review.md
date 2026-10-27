# Revisión de código — B-ADV-0013

**Veredicto: APROBADO. Media: 9/10.** Sin hallazgos pendientes.

Fecha: 2026-10-27. Revisor: Hades. Modo orquestado. Agente y `/review-code` de la instalación 0.6.1; modelo del frontmatter ignorado. Segunda ronda de código: sustituye el rechazo anterior, con C-01 a C-03 resueltos.

## Alcance

Revisión por lectura de todo el delta de producción/documentación respecto a `780ab73d9a18a78cf47a63ffaea9db936a62e826`: `skills/orquestar/orquestar.py`, `skills/orquestar/SKILL.md`, README, CHANGELOG, `docs/orquestacion.md`, triaje, diseño y entrada de revisión de versión. Contraste con el contrato aprobado, DEC-ESP-13-01 a 05, escenarios `@B-ADV-0013` y las reglas de capas y stack del plan de plataforma. Se comprueban las correcciones y su efecto sobre el conjunto del delta, sin implementar.

Se consume `/review-test` vigente APROBADO 9/10 tras la regresión de C-01, sin reevaluar las pruebas ni los informes propios. B-ADV-0020 y T-ADV-0031, también presentes respecto a la base, son entradas de trabajo futuro; no introducen implementación de esas funcionalidades en este delta. No se convierten sus criterios en requisitos de B-ADV-0013.

## Análisis estático y evidencia

Se reutiliza `orquestar_evidencias.jsonl`, árbol `b033d549ea6ffc67546a2229cb501a72b32a2fab`, con código 0 en las cuatro verificaciones:

| Verificación | Hora | Resultado |
| --- | --- | --- |
| Regresión de rechazos previos de `RecuperacionAnalisisTests` y caso de escalada de desarrollo de `EscaladaTests`, ejecutados juntos | 09:37:09 | Verde |
| `git diff --check` | 09:37:15 | Verde |
| `python -m unittest discover -s skills/orquestar -p test_recarga.py` | 09:37:16 | 11 pruebas en verde |
| `python -m unittest discover -s tests -p test_orquestar.py` | 09:38:36 | 80 pruebas en verde |

Sin linter ni tipador configurados. Sintaxis e imports cubiertos por carga de módulos en unittest. Sin manifiestos ni dependencias nuevos: auditoría de dependencias no aplicable. Inspección de secretos por lectura del delta: no se observan credenciales ni tokens incorporados. El código nuevo no introduce ejecución de shell ni nuevas fuentes externas de órdenes. No se relanza ninguna verificación, suite completa ni proveedor real. El rojo anterior solo identifica el antecedente de la regresión, no sustituye el verde actual.

## Puntuaciones

| Criterio | Nota | Motivo |
| --- | --- | --- |
| Corrección | 9/10 | Orden de perfiles independiente de rechazos previos, recuperación por par, reinicio y agotamientos coherentes con el contrato. |
| Seguridad | 9/10 | Sin secretos detectados ni nuevas superficies de ejecución; reutiliza transporte y persistencia existentes. |
| Conformidad | 9/10 | Cumple el triaje y diseño actualizado; mantiene stdlib, capas y mecanismos de desarrollo y recuperación operacional. |
| Calidad | 9/10 | Helpers acotados, estado explícito y separación de las dos causas de escalada. |
| Eficiencia | 9/10 | Construcción única por par y deduplicación con conjunto; recorrido lineal y sin servicios nuevos. |
| Documentación | 9/10 | Regla general y vista operativa sincronizadas; textos y enlace restaurados; impacto del cambio de prueba documentado. |

**Media: 9/10 (> 8), sin hallazgos críticos ni altos.**

## Reevaluación de hallazgos

### C-01 — ALTA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

`cadena_analisis` obtiene el inicial mediante `rol_de` con dificultad y paso; ya no recibe el ID ni consulta escalada por rechazos. Construye niveles superiores, escalada sobre el inicial y reservas de ese inicial antes de deduplicar. Una reserva propia de escalada no sustituye las reservas finales de la cadena.

`bucle` limita la llamada a `escalada` por rechazos a pasos fuera de `PASOS_ANALISIS`. Para análisis, `escalado` permanece falso y se retira del entorno cualquier `ORQUESTAR_ESCALADA` heredado. `revisar-tarea` mantiene su rol Artemisa, pero sus rechazos previos ya no adelantan la escalada de la recuperación por falta de progreso. `task-dev` y `bug-fix` conservan su promoción y escalada anteriores.

La regresión con dos rechazos y reserva exclusiva de escalada pasa en el árbol actual, junto con el caso de escalada de desarrollo trasladado a `task-dev`. El diseño declara ese impacto y la separación de circuitos. La corrección elimina la causa señalada, sin ampliar el contrato.

### C-02 — MEDIA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

La regla general de `skills/orquestar/SKILL.md` y la vista de `docs/orquestacion.md` describen ahora el agotamiento de perfiles, el límite por perfil y los desenlaces local/global. Conservan la promoción y bloqueo de desarrollo y la recuperación propia del cierre de suite. Desaparece la afirmación general de parada tras dos intentos que contradecía la sección nueva.

### C-03 — BAJA — Resuelto

**Para:** desarrollador. **Destino:** resolver. **Estado vigente:** resuelto, sin acción pendiente.

Las adiciones del README, skill, CHANGELOG, triaje y revisión de versión restauran las palabras y flechas en UTF-8. El fragmento `#recuperación-de-análisis-sin-progreso` del README corresponde al encabezado final de la skill. Los errores históricos ajenos a las adiciones no se incorporan a esta corrección.

## Resto del delta y hallazgos nuevos

Sin hallazgos nuevos. La cadena aplica herencia y ajustes antes de comparar harness/model/effort, conserva la primera aparición y no expande recursivamente reservas de niveles o escalada. Los globales parten de media por defecto; los niveles no reescriben dificultad del backlog.

La recuperación se indexa por `(paso, argumento normalizado)` y conserva perfiles, índice, intentos y marca de inicio al intercalar pares y transferir por JSON. Cada cambio de perfil reinicia contador y fuerza una sesión nueva en su primera ejecución. El progreso elimina solo la recuperación activa, también si hay avance commiteado pese al retorno erróneo del arnés.

El agotamiento de `especificar` y `revisar-tarea` persiste diagnóstico y bloqueo del ID, avisa y vuelve al selector para continuar independientes; las dependientes siguen sujetas al selector existente. Los otros cinco pasos paran con diagnóstico sin cambiar estados del backlog. El contexto opcional añadido a `bloquear_sin_progreso` conserva su comportamiento para los llamantes que no lo proporcionan.

Las ramas de cuota, espera y fallos operacionales siguen precediendo al consumo de intentos por falta de progreso. Se conservan sus reservas y la detección de progreso commiteado. La rama de desarrollo mantiene sus promociones y bloqueo. No se observa una regresión adicional por lectura y evidencia aportada. El estado permanece local y usa stdlib; no hay desviación de arquitectura que requiera una DEC nueva.

## Enrutado y límites

C-01, C-02 y C-03 resueltos; **sin destino correctivo pendiente** para desarrollador, especificador o humano. La aprobación cubre el delta revisado y las verificaciones indicadas, sin afirmar ejecución con proveedores reales ni suite completa. Se actualiza únicamente este informe, sin cambiar código, estados ni crear commits.
