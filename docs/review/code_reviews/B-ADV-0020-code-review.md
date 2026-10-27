# Revisión de código B-ADV-0020

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo: orquestado. Ronda 2.

## Alcance y método

Base estable: 3f53a3c7ecd707733e58cecf5041bf3d25def4b9. Se revisa el delta COMPLETO de producción en skills/orquestar/orquestar.py y documentación README.md, CHANGELOG.md, docs/orquestacion.md y skills/orquestar/SKILL.md. Se contrasta con el BDD aprobado, el contrato/triaje del bug, docs/design/B-ADV-0020-design.md y docs/requirements/platform_plan.md. Se reevaluan C1–C3 del informe anterior y se examina el conjunto del delta por posibles regresiones. Los informes no se consideran producción y los tests se juzgan separadamente en review-test, ronda 4, APROBADO.

Se aplican Hades y review-code instalados en C:/Users/Iván Moreno/.adevv/versions/0.6.1, ignorando el modelo. No se corrige código ni diseño y no se modifica el estado in_progress. El cierre documental y de validación anunciado por el invocador queda fuera de esta edición de informes.

## Conformidad y alcance funcional

- La clasificación de ejecución distingue hora real, sospecha sin hora y créditos. El parser conserva su valor público compatible; la ejecución usa intervalo positivo finito, 300 por defecto. Las marcas históricas de 1800 se interpretan como supuestas y las demás conservan su plazo.
- El plegado de recuperaciones conserva los tokens y el JSONL. Éxito/reset añaden eventos por par; el selector modelo/arnés/global no reescribe el histórico ni selecciona pares ajenos.
- La selección conserva prioridad de titular y reservas; respeta cuotas reales e intervalos supuestos también con un único perfil o con todas las reservas agotadas. Las sospechas pueden comprobarse al relanzar.
- Estado e informe de agentes comparten certeza, origen y recuperación. La CLI del reset sale antes de iniciar bucle/gateway.
- La espera de cuota comprueba recuperaciones antes del primer sleep y después, con polling máximo de 30 segundos y prioridad de parada. Las esperas operacionales mantienen su circuito.

El diseño incorpora explícitamente las instantáneas opcionales, el contexto opcional de espera y los llamantes afectados; no se detectan divergencias sin documentar. Se conserva el motor único de skills/orquestar, stdlib, JSONL y el despacho existente, conforme a las reglas de capas y DEC-P09/P10 de plataforma. No cambia la arquitectura, las dependencias ni la instalación. La documentación de usuario describe los cambios de contrato y sus órdenes sin mantener el antiguo fallback de ejecución de 30 minutos.

## Análisis estático y evidencia

Se reutilizan registros --verificar de orquestar_evidencias.jsonl del árbol **9b62e379a8a402c89f2f16b8768da49820133d29**:

- 10:08:08: test_arnes_ausente, test_fallos_arnes y test_*cuota*, código 0.
- 10:08:09: tests específicos de reanudación y cuota del subagente en tests.test_orquestar, código 0.
- 10:09:04: compilación de TODOS los siete Python modificados, código 0.
- 10:09:05: git diff --check, código 0.
- 10:09:20: test_informe_agentes, código 0.
- 10:09:30: test_estado_agentes, código 0.

La ejecución completa de tests.test_orquestar se está renovando: su verde final no consta en la evidencia consultada y no se sustituye por el de otro árbol. El antecedente funcional rojo de C1–C3 está descrito en review-test y no se presenta como fallo pendiente del árbol actual.

No se relanzó ningún comando de verificación ni suite completa, ni se ejecutaron módulos fuera del triaje. No hay lint/tipado/secret scanner configurados. No cambian dependencias ni se añaden credenciales o accesos a secretos. El selector se compara con claves de métricas sin introducir órdenes de shell. La aprobación es de revisión; no declara concluida la validación de cierre del invocador.

## Reevaluación de hallazgos anteriores

### C1 — 🟠 ALTA — RESUELTO: coherencia entre cuotas y detalle

- **Evidencia:** configuraciones_con_cuota (1041 y siguientes) captura un instante y unas filas y los pasa tanto a consumo_cuotas como a marcas_cuota. informe_agentes (2185 y siguientes) aplica la misma política. consumo_cuotas admite filas opcionales (2129), conservando el retorno y los llamantes existentes.
- **Evaluación:** las claves de cuotas y marcas proceden de la misma instantánea, por lo que una recuperación añadida entre los cálculos ya no elimina una clave solo de uno de ellos. La vista puede reflejar la instantánea anterior hasta la siguiente consulta, sin mezclar generaciones ni provocar el KeyError señalado.
- **para:** desarrollador, asignación satisfecha.
- **destino:** resolver — completado; sin acción pendiente.

### C2 — 🟠 ALTA — RESUELTO: reset previo al comienzo de la espera

- **Evidencia:** bucle captura contexto_cuota con índice del JSONL y pares del paso antes de seleccionar (2553 y siguientes), y lo entrega a esperar mediante cuotas_esperadas (2740). esperar (1663–1687) revisa desde ese índice los eventos de recuperación para los pares del contexto y los pares con cuota registrada en el intervalo, incluidos subagentes. La comprobación se realiza antes de sleep y tras la comprobación prioritaria de PARADA. Conserva la detección de desaparición durante la espera y condiciona todo este tratamiento al motivo sin cuota.
- **Evaluación:** el reset que ocurre después de calcular el plazo y antes de entrar en esperar queda en el tramo de eventos observado; no depende de que la marca siga presente al capturar pendientes. La firma mantiene compatibles las llamadas sin contexto y las esperas por otros motivos. El diseño documenta el nuevo flujo y los llamantes.
- **para:** desarrollador, asignación satisfecha.
- **destino:** resolver — completado; sin acción pendiente.

### C3 — 🟡 MEDIA — RESUELTO: supresión de avisos por antecedentes ajenos

- **Evidencia:** el bloque de espera (2724–2738) reúne el perfil que motiva la espera y las cuotas de subagentes recién registradas con ese plazo. Solo suprime el aviso genérico si alguna de esas causas mantiene una marca vigente de sin créditos; ya no examina todos los antecedentes como causas del aviso.
- **Evaluación:** una marca de créditos vencida o ajena a la espera real de otro perfil deja de ocultar su notificación. Se conserva el aviso específico por episodio de fallo_cuota y su rearme mediante éxito/reset.
- **para:** desarrollador, asignación satisfecha.
- **destino:** resolver — completado; sin acción pendiente.

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Corrección | 9/10 | Las correcciones eliminan las incoherencias señaladas y mantienen selección, persistencia y recuperación del contrato. |
| Seguridad | 9/10 | Sin nuevas superficies de shell, secretos o dependencias; reset limitado a pares existentes. |
| Conformidad | 9/10 | Fiel al BDD, triaje, mapa de impacto actualizado y plataforma. |
| Calidad | 9/10 | Helpers compartidos, extensiones opcionales compatibles e instantáneas coherentes. |
| Eficiencia | 8/10 | Plegados lineales y polling acotado; siguen existiendo lecturas del histórico por par de reset, razonables a la escala documentada. |
| Documentación | 9/10 | Guías y diseño reflejan intervalo, compatibilidad, episodios, selector y espera. |

**Media: 8,83/10.** Sin hallazgos críticos ni altos pendientes.

## Hallazgos nuevos y salida para el bucle

No se detectan hallazgos nuevos que requieran acción en el alcance completo revisado. **APROBADO. C1, C2 y C3 resueltos.** Sin enrutado pendiente. El bug conserva su estado y el cierre corresponde al flujo del invocador, incluida la evidencia funcional final aún en renovación. No se realizan commits ni modificaciones fuera de los dos informes autorizados.
