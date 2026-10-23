# Revisión de Pruebas (`review-test`): T-ADV-0004 (Ronda 2)

- **Tarea**: T-ADV-0004 — Actualización automática de versiones publicadas
- **Especificación BDD**: `tests/features/actualizacion_automatica.feature`
- **Archivos auditados**:
  - `tests/test_updater.py`
  - `tests/test_processes.py`
- **Veredicto**: **APROBADO**

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Cobertura** | 9.5 / 10 | Cubre los 16 escenarios de `actualizacion_automatica.feature` (`@CA-F03-01` a `@CA-F03-16`), incluyendo los 10 ejemplos de la tabla de ventana de comprobación, fallos de instalación, arneses desfasados, detección y clasificación de procesos y subcomando `adevv actualizar`. |
| **Aserciones** | 9.0 / 10 | Las aserciones verifican estados persistidos (`active.json`, `config.json`, `update_state.json`), mensajes exactos en `stdout`/`stderr`, códigos de salida, argumentos de subprocesos (`timeout=5`, variables de entorno sin prompts interactivos) y limpieza/preservación selectiva de versiones en disco. |
| **Rojo correcto** | 9.5 / 10 | Las 24 pruebas se ejecutan con lint y tipado limpios: 3 pasan en `test_processes.py` y las 21 restantes fallan en rojo por `NotImplementedError` en `adevv.updater` y ausencia del subcomando `actualizar` en `adevv.cli`. |
| **Estabilidad** | 9.5 / 10 | Pruebas deterministas, aisladas mediante `TemporaryDirectory` y `ADEVV_HOME`, con tiempo inyectado (`ahora`) y repositorios Git locales sin dependencia de red real. |
| **Media** | **9.38 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Reevaluación de Hallazgos de la Ronda 1

- **H-01 (🔴 CRÍTICO — Escenarios `@CA-F03-08` y `@CA-F03-10` sin cobertura de pruebas)**: **`resuelto`**. Se añadieron `test_ca_f03_08_fallo_instalacion_durante_comprobacion_automatica` (verifica transición a `FALLIDA`, persistencia en `update_state`, mensaje en `stderr` y continuación de `adevv orquestar --fondo` con la versión `0.1.0`) y `test_ca_f03_10_actualizacion_aplicada_con_arnes_desfasado` (verifica `APLICADA` y el detalle de arneses sin sincronizar en el mensaje).
- **H-02 (🟠 ALTA — Cobertura y aserciones incompletas en `@CA-F03-02`, `@CA-F03-03`, `@CA-F03-04`, `@CA-F03-05` y `@CA-F03-12`)**: **`resuelto`**. Se incorporaron `test_ca_f03_02_actualizacion_aplicada_al_lanzar` (verifica el aviso en `stderr`, el despacho con la ruta de la `0.2.0` recién activada y la salida de `adevv --version`), `test_ca_f03_03_transicion_inicial_a_aplazada` (primera detección con bucle en `C:\SW\Afinn`, persistencia de `aplazada` y aplicación sin esperar 24 h al terminar el bucle), `test_ca_f03_04_y_05_adevv_actualizar_sin_argumentos_bucle_y_gateway` (bloqueo por bucle previo a la migración y actualización permitida con gateway en marcha, además de la preservación en disco de la carpeta `0.1.0` usada por el gateway en `test_instalar_version_publicada_exito_y_limpieza`) y las aserciones completas en `test_ca_f03_12_volver_atras_y_reactivar`.
- **H-03 (🟠 ALTA — Aserciones insuficientes en `@CA-F03-06` y en `test_processes.py`)**: **`resuelto`**. En `test_consultar_versiones_publicadas_timeout_y_credenciales` se comprueban `timeout=5`, las variables de entorno `GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never` y `GIT_ASKPASS=echo`, y la continuación de `adevv orquestar --estado` sin aviso en el primer fallo de red; en `tests/test_processes.py`, `test_filtro_proceso_actual_y_padre` ejecuta la lógica real de `detectar_procesos_adevv` mockeando únicamente `subprocess.run`.

---

## Hallazgos Nuevos

Ninguno.
