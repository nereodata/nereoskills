# Revisión de Código: T-ADV-0017

- **Tarea**: `docs/plan/tasks/T-ADV-0017-canal-limpio-de-prompts-en-subagentes.md`.
- **Diseño**: `docs/design/T-ADV-0017-design.md`.
- **Producción revisada**: `skills/orquestar/orquestar.py` y `skills/orquestar/SKILL.md`.
- **Arquitectura**: `docs/requirements/platform_plan.md`, especialmente `DEC-P03` y `DEC-P09`.
- **Revisor**: Hades.
- **Fecha**: 2026-10-23.
- **Ronda**: 2; reevaluación de H-01 y de los efectos de su corrección.
- **Veredicto**: **APROBADO**.
- **Puntuación media**: **9.00 / 10**. Sin hallazgos críticos ni altos pendientes.

## Análisis estático y evidencias

- **Compilación**: el invocante aporta `python -m py_compile skills/orquestar/orquestar.py skills/orquestar/test_agente_prompt.py` en verde.
- **Whitespace**: el invocante aporta `git diff --check` en verde.
- **Verificación del triaje**: el invocante aporta 20 pruebas en `test_agente_prompt.py`, 8 en `test_estado_agentes.py` y 5 en `RolesTests`, todas en verde. Incluye regresiones declaradas para nombres con guiones iniciales, errores de Git y preservación desde `main()`.
- **Secretos y dependencias**: no se observan credenciales ni dependencias externas añadidas en el delta de producción.
- **Linter / tipado**: N/A; la tarea declara que no están configurados.
- Se acepta la evidencia aportada sin repetir pruebas ni comprobaciones estáticas. La reevaluación se realiza mediante lectura del código y su contexto de llamada; no se reauditan las pruebas.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Corrección | 9 | La consulta distingue ausencia de seguimiento de errores indeterminados; el llamador solo autoriza limpiar archivos de raíz cuando el helper devuelve `False`. |
| Seguridad | 9 | El separador `--` protege los nombres con guiones iniciales; los errores operativos y las excepciones conservan el archivo. |
| Conformidad | 9 | Cumple la preservación exigida por el apartado 4 del diseño y mantiene el alcance y las decisiones de plataforma. |
| Calidad | 9 | Corrección localizada, legible y sin duplicación significativa. |
| Eficiencia | 9 | Mantiene una consulta Git por archivo candidato de raíz, sin dependencias nuevas. |
| Documentación | 9 | La skill describe `--prompt`, la limpieza de temporales y la exclusión de `orquestar_prompt.txt`; la corrección sostiene la garantía de preservación revisada. |

## Reevaluación de hallazgos anteriores

### H-01 — 🟠 ALTA — **resuelto**

- **Problema anterior**: un error de opciones o un fallo operativo de Git podía clasificar un archivo rastreado como no rastreado y autorizar su borrado.
- **Evidencia de corrección**: en `skills/orquestar/orquestar.py:1385`, la orden es ahora `['git', 'ls-files', '--error-unmatch', '--', arg_ruta]`. El nombre que comienza por `--` se transmite después del separador de opciones.
- **Discriminación de resultados**: las líneas 1391–1397 devuelven `False` únicamente ante código 1 y el diagnóstico `did not match any file` en stderr. Código 0 devuelve `True`; cualquier otro resultado o excepción también devuelve `True`, impidiendo autorizar la limpieza ante incertidumbre. Un diagnóstico traducido que no coincida conserva igualmente el archivo.
- **Efecto en el llamador**: la condición de la línea 1629 requiere tanto el padre resuelto igual a la raíz como un resultado `False` del helper. Ante un fallo operativo, `borrar_prompt_file` permanece falso y el `finally` no elimina el archivo.
- **Conformidad**: el tratamiento conservador refina la regla general del apartado 3 del diseño sobre fallos de Git para cumplir su garantía explícita del apartado 4: preservar los archivos rastreados. No altera interfaces, arquitectura ni política de limpieza del resto de rutas.

## Hallazgos nuevos

Ninguno.

## Alcance de la revisión

Se compara la corrección actual con el H-01 del informe previo y se comprueba su integración con la autorización y ejecución de la limpieza. La corrección queda confinada al helper; no requiere ampliar la reevaluación a otros módulos. No se modifica código, diseño ni pruebas.
