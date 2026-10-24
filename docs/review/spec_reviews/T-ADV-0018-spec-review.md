# Revisión de Especificación: T-ADV-0018

- **ID Maestro**: T-ADV-0018
- **Tarea**: [`docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md`](../../plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md)
- **Especificación revisada**: Alcance de definición completo e impedimento previo a BDD en [`docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md`](../../plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md#L17-L38) frente a [`tests/features/actualizacion_automatica.feature`](../../../tests/features/actualizacion_automatica.feature#L52-L58), [`docs/requirements/funcionalidades/F-03_actualizacion_automatica.md`](../../requirements/funcionalidades/F-03_actualizacion_automatica.md#L21-L122) y [`docs/requirements/platform_plan.md`](../../requirements/platform_plan.md#L177-L185)
- **Veredicto**: **RECHAZADO**
- **Puntuación media**: **4.75 / 10**

## Comprobaciones Obligatorias

- ✅ **No regresión**: No se eliminan ni alteran escenarios existentes en `tests/features/`.
- ❌ **Coherencia**: **Fallo crítico**. `T-ADV-0018` (`origen` l. 10, `Objetivo de Negocio` l. 18, `CA-M-2` l. 22 y `CA-M-3` l. 23) exige que `gateway.py` y `orquestar.py` se reemplacen automáticamente al cambiar `~/.adevv/active.json` «sin requerir reinicio manual», mientras que los contratos vigentes de requisitos, BDD y plataforma ([`tests/features/actualizacion_automatica.feature:52-58`](../../../tests/features/actualizacion_automatica.feature#L52-L58) `@CA-F03-05`, [`docs/requirements/funcionalidades/F-03_actualizacion_automatica.md:21,48,57,116-122`](../../requirements/funcionalidades/F-03_actualizacion_automatica.md#L21), [`docs/requirements/requirements.md:73,111,121`](../../requirements/requirements.md#L73), [`docs/requirements/req_analysis.md:35`](../../requirements/req_analysis.md#L35) `DEC-03` y [`docs/requirements/platform_plan.md:12,27,161,177,185`](../../requirements/platform_plan.md#L177) `DEC-P01`/`DEC-P09`) fijan que los gateways en marcha permanecen en la versión con la que arrancaron hasta su reinicio manual. Asimismo, el triaje declara `Subfase A: Definición [EXEC]` (`l. 28`), lo que exigiría modificar `tests/features/` fuera de las rutas permitidas por el mandato (`skills/`, `agents/` y `workflows/`).
- ❌ **Trazabilidad**: **Fallo crítico**. No existen escenarios BDD (`.feature`) que tracen `@CA-M-1`..`@CA-M-4` ni exención `[SKIP]` respaldada en `platform_plan.md` debido a la parada preventiva en Subfase A conforme a `/generate-bdd` (`skills/generate-bdd/SKILL.md:44-46,56-59`).
- ❌ **Delta real**: **Fallo crítico**. La tarea está detenida en el triaje sin especificación ejecutable consolidada debido al conflicto documental entre contratos y la restricción de rutas.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Claridad** | 7.0/10 | Los criterios `CA-M-1`..`CA-M-4` son claros sobre el mecanismo en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`, pero colisionan con la invariante documentada en `F-03`/`DEC-P01` y presentan pérdida de tildes (`?`) en el bloque de triaje. |
| **Completitud** | 2.0/10 | Bloqueado antes de generar BDD; falta conciliar en la especificación/arquitectura cómo coexiste la auto-recarga entre ciclos con `CA-F03-05`/`RF-F03-08` y con las rutas autorizadas (`skills/`, `agents/`, `workflows/`). |
| **Testeabilidad** | 5.0/10 | `CA-M-4` define pruebas unitarias claras en `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/test_recarga_gateway.py`, pero `Subfase A [EXEC]` no es ejecutable sobre `tests/features/` sin violar las rutas autorizadas ni las reglas de integridad de `/generate-bdd`. |
| **Estructura** | 5.0/10 | El impedimento fue correctamente detectado y detenido antes de alterar escenarios existentes, pero requiere ajuste del especificador antes de continuar. |
| **Media** | **4.75/10** | **RECHAZADO** (media ≤ 8 y con hallazgos 🔴 CRÍTICO). |

## Hallazgos

### 1. 🔴 CRÍTICO — Contradicción documental entre `T-ADV-0018` (`CA-M-2`/`CA-M-3`) y `RF-F03-08` / `CA-F03-05` / `DEC-P01`, e inviabilidad de `Subfase A [EXEC]` bajo las rutas autorizadas
- **Ubicación**:
  - [`docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md:10,18,21-24,28,37-38`](../../plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md#L10-L38)
  - [`tests/features/actualizacion_automatica.feature:52-58`](../../../tests/features/actualizacion_automatica.feature#L52-L58) (`@CA-F03-05 @RF-F03-08`)
  - [`docs/requirements/funcionalidades/F-03_actualizacion_automatica.md:21,48,57,116-122`](../../requirements/funcionalidades/F-03_actualizacion_automatica.md#L21-L122) (`RF-F03-08`, fila `E11`, casos límite y `CA-F03-05`)
  - [`docs/requirements/requirements.md:73,111,121`](../../requirements/requirements.md#L73-L121) y [`docs/requirements/req_analysis.md:35`](../../requirements/req_analysis.md#L35) (`DEC-03`)
  - [`docs/requirements/platform_plan.md:12,27,161,177,185`](../../requirements/platform_plan.md#L177-L185) (`DEC-P01`, `DEC-P09`)
- **para**: `especificador`
- **destino**: `resolver`
- **Evaluación del impedimento**:
  1. **Existe contradicción documental real que el desarrollador no está autorizado a resolver por su cuenta**: `RF-F03-08` (`docs/requirements/funcionalidades/F-03_actualizacion_automatica.md:21`), el caso límite de la línea 57 («sigue con su versión y el aviso pide reiniciarlo»), `CA-F03-05` (`tests/features/actualizacion_automatica.feature:52-58`: «Y el gateway sigue respondiendo con la 0.1.0 / Y el mensaje incluye "Reinicia el gateway en C:\SW\Adevv."»), `requirements.md:73,121`, `DEC-03` (`req_analysis.md:35`) y `DEC-P01` (`platform_plan.md:177`) establecen que los gateways en marcha siguen ejecutando su versión inicial hasta reinicio manual. Por su parte, `T-ADV-0018` (`l. 10, 18, 22, 23`) ordena que `gateway.py` (entre vueltas de polling) y `orquestar.py` (entre pasos del bucle) detecten el cambio en `~/.adevv/active.json` y se reemplacen automáticamente por la versión activa sin reinicio manual. Conforme a `skills/generate-bdd/SKILL.md:44-46,56-59`, el desarrollador tiene prohibido sustituir escenarios existentes o decidir por su cuenta entre contratos documentados en conflicto.
  2. **Restricción de rutas en el árbol de trabajo**: El mandato de ejecución restringe los cambios de `task-dev` a `skills/`, `agents/` y `workflows/` (`RF-F02-09`). Mantener `Subfase A: Definición [EXEC]` (`T-ADV-0018:28`) obliga a editar `tests/features/`, que está fuera de las rutas permitidas para el desarrollador, mientras que `DEC-P09` (`platform_plan.md:185`) solo cubre actualmente las ampliaciones operativas de `v0.4`.
  3. **No requiere intervención del `humano`**: No falta ningún recurso externo ni decisión de negocio abierta; la intención de `v0.5.0` en `T-ADV-0018` es inequívoca y ambos contratos son técnicamente compatibles separando el contrato del instalador (`adevv/updater.py`, que no se toca) del contrato de los motores en `skills/` (`orquestar.py` y `gateway.py`).
- **Ajustes concretos que debe realizar el `especificador` (en el paso `especificar`, sin preguntar al humano)**:
  1. **En [`docs/requirements/platform_plan.md`](../../requirements/platform_plan.md#L177-L185) (ampliar `DEC-P09` o añadir `DEC-P10`):**
     - Formalizar que las ampliaciones de `v0.5` en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py` (incluida la auto-recarga cooperativa de `T-ADV-0018` al detectar cambio en `~/.adevv/active.json`) se implementan íntegramente en `skills/` y se verifican con pruebas unitarias en `skills/<skill>/test_*.py` sin modificar `adevv/` ni `tests/features/`.
     - Dejar explícita la compatibilidad con `DEC-P01`, `RF-F03-08` y `CA-F03-05`: durante `adevv actualizar` (y mientras dura cualquier paso de `bucle()` o petición de `escuchar()`), `adevv/updater.py` instala la nueva versión lado a lado en `~/.adevv/versions/<nueva>/`, mantiene intacta `~/.adevv/versions/<anterior>/`, no mata procesos en marcha y conserva el mensaje de aviso y el comportamiento de `CA-F03-05` para procesos que corren versiones previas (`0.1.0`) o siguen en mitad de su ciclo; la recarga a la nueva versión ocurre de forma cooperativa e interna en `skills/telegram_gateway/gateway.py` (al inicio de la siguiente vuelta de polling en `escuchar()`) y en `skills/orquestar/orquestar.py` (al inicio de la siguiente iteración entre pasos en `bucle()`).
  2. **En [`docs/requirements/funcionalidades/F-03_actualizacion_automatica.md`](../../requirements/funcionalidades/F-03_actualizacion_automatica.md#L21-L57) (`RF-F03-08` l. 21 y caso límite l. 57) y [`docs/requirements/requirements.md`](../../requirements/requirements.md#L73-L121) (`§3 R2` l. 73 y `§4` l. 121):**
     - Matizar que el instalador no modifica archivos en uso y los procesos en marcha siguen con su versión durante la instalación y la operación en curso (y hasta reiniciarse en versiones anteriores a `v0.5.0`), sin alterar el escenario `@CA-F03-05` de `tests/features/actualizacion_automatica.feature:52-58`.
  3. **En [`docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md`](../../plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md#L20-L38):**
     - Explicitar en `CA-M-1`..`CA-M-4` la referencia a `DEC-P09`/`DEC-P10` y que no se modifican `adevv/` ni `tests/features/actualizacion_automatica.feature`.
     - Cambiar en el triaje `Subfase A: Definición` a `[SKIP]` (lógica interna de auto-recarga entre iteraciones en `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py` con contrato completo en `CA-M-1`..`CA-M-4`, verificada mediante pruebas unitarias en `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/test_recarga_gateway.py`), eliminando la sección `## Impedimento de definición` (l. 37-38) y devolviendo la tarea a `status: planned` sin `pendiente_de`.

### 2. 🟡 MEDIA — Caracteres `?` en lugar de tildes UTF-8 en las secciones de triaje e impedimento de la tarea
- **Ubicación**: [`docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md:28-38`](../../plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md#L28-L38) (`Definici?n`, `conservaci?n`, `contradicci?n`, `Dise?o`, `Implementaci?n`, `Documentaci?n`, `seg?n`, `Verificaci?n`, `detecci?n`, `a?n`, `autom?tica`, `proh?be`).
- **para**: `especificador`
- **destino**: `resolver`
- **Detalle**: Las líneas añadidas en el triaje e impedimento contienen signos `?` en lugar de caracteres acentuados UTF-8. Al actualizar la tarea en el paso `especificar`, deben escribirse con codificación UTF-8 correcta.
