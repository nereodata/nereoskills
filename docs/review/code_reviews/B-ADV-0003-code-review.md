# Code Review: B-ADV-0003

- **Veredicto**: APROBADO
- **Media**: 9.00 / 10
- **Revisor**: Hades
- **Fecha**: 2026-10-25
- **Alcance**: delta de producción de `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`. Las pruebas quedan fuera de esta revisión. Subfases A, B y E omitidas expresamente en el triaje; no se exige un diseño de tarea ni documentación adicional por esas subfases.

## Análisis estático y evidencia

Reevaluación tras la corrección de H-01. Se acepta la verificación registrada en `orquestar_evidencias.jsonl` sobre el árbol `d771e5f56698e5a02d128e9d8e0c33962f732d66`, identificado por quien solicita la revisión como el árbol recibido. No se han relanzado estas comprobaciones:

- `python -m unittest tests/test_telegram_gateway.py tests/test_orquestar.py skills/orquestar/test_estado_agentes.py`: código 0 (89 tests OK según la evidencia aportada por el solicitante).
- `git diff --check`: código 0.
- `python -m py_compile skills/orquestar/orquestar.py skills/telegram_gateway/gateway.py`: código 0.

Linter y tipador: N/A, sin cambios respecto a la revisión anterior. Auditoría de dependencias: N/A, sin cambios de dependencias. La inspección del delta no detecta secretos incorporados ni nuevas interpolaciones de órdenes de shell.

La reevaluación se ha realizado por lectura del informe anterior, del delta de producción, de los consumidores del resolver y del plan de plataforma. Se ha comprobado el cierre de H-01 y que la corrección conserva la prioridad del PATH actual, los respaldos de Windows y la tolerancia a errores de acceso al registro. La gestión del 409 no cambia respecto a la ronda anterior. No se han ejecutado pruebas ni experimentos ni modificado código de producción.

## Puntuaciones

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| **Corrección** | 9 / 10 | El resolver expande las variables del Path del registro antes de dividirlo y las rutas añadidas antes de buscar, manteniendo la prioridad del PATH actual. El 409 se registra y propaga al bucle, que detiene la escucha sin propiedad del PID o al tercer conflicto consecutivo; `main()` conserva la limpieza en `finally`. |
| **Seguridad** | 9 / 10 | Las rutas consultadas pertenecen al usuario; no se escriben credenciales ni se añaden órdenes de shell. La limpieza solo retira marcas cuando el PID pertenece al proceso actual. |
| **Conformidad** | 9 / 10 | Los cambios corresponden al triaje C2 y respetan las capas y el uso de biblioteca estándar del plan de plataforma (`DEC-P03`, `DEC-P09`). La recuperación mediante el Path de usuario incluye ahora sus variables de entorno. No se observa una decisión arquitectural nueva que requiera DEC. |
| **Calidad** | 9 / 10 | Resolver común reutilizado por `comando()`, `agente()` e `invocar()`; comprobación de propiedad extraída a un helper breve. La gestión del conflicto queda localizada en la frontera HTTP y el bucle. |
| **Eficiencia** | 9 / 10 | Solo se consulta el registro tras fallar la búsqueda normal; trabajo acotado por el número de rutas. Los conflictos mantienen una espera entre intentos y un límite de tres conflictos consecutivos para el propietario. |
| **Documentación** | 9 / 10 | Los helpers añadidos tienen docstrings y el log describe el conflicto. No se observan comandos u opciones documentados que queden falsos por el delta. |

## Reevaluación de hallazgos anteriores

### H-01 — resuelto (severidad anterior: 🟠 ALTA)

- **Ubicación**: `skills/orquestar/orquestar.py`, función `buscar_ejecutable()`.
- **Responsable de la corrección**: `desarrollador`.
- **Evidencia de cierre**: el valor del registro pasa por `winreg.ExpandEnvironmentStrings()` cuando está disponible, con `os.path.expandvars()` como alternativa, antes de dividirse en rutas. Además, cada ruta añadida pasa por `os.path.expandvars()` al construir el PATH de búsqueda. Aunque la expansión del registro no se condiciona a su tipo, cubre el caso `REG_EXPAND_SZ` que originó el hallazgo.
- **Validación aceptada**: el solicitante identifica el caso `test_buscar_ejecutable_expands_registry_variables_such_as_userprofile`, con `%MY_CUSTOM_DIR%/custom_bin` fuera de los respaldos fijos y PATH vacío, dentro de la suite registrada con código 0 para este árbol. La valoración del cierre se apoya en la lógica de producción y en esa evidencia; no se realiza una revisión de pruebas en esta skill.
- **Regresiones de la corrección**: no se detectan. La búsqueda normal sigue ejecutándose primero y la expansión queda localizada en las rutas de respaldo de Windows.

## Hallazgos nuevos

Ninguno. No quedan hallazgos críticos ni altos abiertos. La media es superior a 8 y el delta queda aprobado.
