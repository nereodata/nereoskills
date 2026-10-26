# Revisión de código — B-ADV-0006

**Veredicto: APROBADO** — Reevaluación del delta completo y de H1–H4.

## Alcance y evidencia

Aplicadas las instrucciones de Hades y `/review-code` de la instalación 0.6.0, ignorando el modelo del frontmatter. Revisado el delta completo respecto a `HEAD` de `skills/orquestar/orquestar.py`, `skills/orquestar/SKILL.md`, el documento del bug, `CHANGELOG.md` y `docs/review/versions/v1.0-revision.md`, junto al diseño actualizado `docs/design/B-ADV-0006-design.md` y el plan de plataforma. Se reutilizan las aprobaciones de especificación y pruebas, ambas de 9/10; no se reabre su revisión.

Evidencia de `orquestar_evidencias.jsonl` sobre el árbol **`671a1a0139d6e387092ae685a1e3d058ea7d2c4f`**, registrada el 2026-10-26:

- `python -m unittest discover -s tests -p test_orquestar.py > .git/B-ADV-0006-motor.log 2>&1`: código 0. El log confirma **70 tests, OK**.
- `python -m py_compile tests/test_orquestar.py skills/orquestar/orquestar.py`: código 0.
- `git diff --check`: código 0.

No se han relanzado comprobaciones, pruebas ni suite completa. La evaluación combina lectura del delta, contratos de sus colaboradores y evidencia ya disponible. No se ha modificado producción ni pruebas. El cambio a `completed` y el cierre del apartado Hades de la revisión de versión corresponden al paso final previo al commit, según lo indicado; no son requisitos pendientes para este veredicto.

## Análisis estático y seguridad

- Compilación y comprobación del diff: verdes, reutilizadas del mismo árbol.
- Linter, tipado y escáner de secretos: no configurados para este delta.
- Inspección manual de secretos: no se detectan credenciales, tokens ni claves incorporados en el delta. El comando proviene de la configuración del operador; la salida se guarda como texto y no se ejecuta.
- Dependencias y arquitectura: sin dependencias nuevas. `hashlib` pertenece a stdlib; se conserva el motor único y no se modifica el parser ni el transporte compartidos. No se observa desviación del stack o de las reglas de capas del plan de plataforma.

## Evaluación del conjunto

- **Captura y compatibilidad:** `verificar` mantiene firma y retorno entero, combina stdout/stderr en archivo temporal y lee su cola de 32768 bytes. Guarda comando, árbol, código y salida, y muestra la cola al terminar. La reutilización verde sigue ligada al mismo árbol y comando.
- **Recuperación y persistencia:** el cierre rojo registra un bug elegible en la versión correspondiente, con prefijo y ruta de backlog configurados. La identidad combina versión normalizada, marcador de cierre y SHA-256 del comando UTF-8. El comando completo permanece en el cuerpo. Se actualiza la sección de evidencia sin sustituir el resto del trabajo y se commitea únicamente el archivo del bug antes del agente.
- **Contadores y promoción:** el fallo inicial no consume intento; las recaídas incrementan solo tras `completed`. `suite_dificultad` separa niveles y permite reiniciar el contador cuando actúa la promoción ordinaria. Al tercero se usa el mecanismo existente de promoción; en dificultad máxima se bloquea para humano y se devuelve un motivo de parada.
- **Bloqueos y avisos:** `blocked` y `cancelled` no se reabren. Los motivos nuevos usan los últimos 1200 caracteres; la salida capturada se conserva en evidencia y, en el alta/reapertura, en el bug. Se mantiene el camino de consola y Telegram por `parar`, con la adaptación del mensaje comprobada por las regresiones aprobadas.
- **Rama y continuidad:** la release seleccionada se activa antes de verificar el cierre tanto en PASO como en PARAR, con guardia de cambios pendientes antes del checkout. Tras registrar el fallo se recalcula el estado y se continúa por el flujo normal; la revisión requiere volver al cierre y obtener un verde. Se mantienen selección de perfiles y revisiones habituales.
- **Documentación:** el diseño y triaje declaran el hash y la cola de avisos, el contrato operativo explica las repeticiones de suite y la caché, y el changelog y revisión de versión reflejan el alcance. La sustitución del test del contrato anterior está documentada expresamente.

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Corrección | 9/10 | Identidad estable, recuperación persistida y límites por dificultad coherentes con el contrato. |
| Seguridad | 9/10 | Sin secretos incorporados ni nueva ejecución del texto de salida. |
| Conformidad | 9/10 | Sigue el triaje, diseño actualizado y plataforma; correcciones de QA documentadas. |
| Calidad | 9/10 | Cambio localizado y reutilización de selección, promoción y avisos existentes. |
| Eficiencia | 9/10 | Captura temporal, lectura acotada y conservación de la caché por contenido. |
| Documentación | 9/10 | Contrato operativo y diseño consistentes con recuperación, evidencia y avisos acotados. |

**Media: 9/10.** Sin hallazgos críticos ni altos pendientes.

## Reevaluación de hallazgos anteriores

El [informe inicial](B-ADV-0006-hallazgos.md) se conserva como histórico superado.

| Hallazgo | Estado | Evidencia de resolución | Para | Destino |
| --- | --- | --- | --- | --- |
| H1 — Escapes e identidad sin PyYAML | **Resuelto** | `suite_clave` contiene el SHA-256 hexadecimal del comando UTF-8, usado en la búsqueda. No depende de desescapar YAML; el comando completo sigue en el cuerpo. La regresión sin PyYAML y con comillas/barras conserva ID y contadores. | desarrollador | resolver — cerrado |
| H2 — Aviso largo de Telegram | **Resuelto** | Los dos motivos de parada usan `cola_aviso = salida[-1200:]`, manteniendo la evidencia capturada en disco. La regresión aprobada recorre `parar` y `avisar` hasta el envío simulado, comprueba longitud UTF-16 con prefijo/firma y conservación de la última línea y evidencia. | desarrollador | resolver — cerrado |
| H3 — Cobertura del cambio de rama | **Resuelto** | Las regresiones aprobadas cubren PASO y PARAR desde otra rama, orden de verificación y agente en la release, commit en esa rama y bloqueo previo ante árbol sucio. Incluidas en los 70 tests verdes. | desarrollador | resolver — cerrado |
| H4 — Frecuencia documentada de suite | **Resuelto** | El párrafo de verificación elimina «una sola vez por versión» y explica la repetición tras arreglos y la reutilización del verde para el mismo árbol/comando. | desarrollador | resolver — cerrado |

## Hallazgos nuevos

Ninguno. No se requiere intervención humana ni se identifica deuda nueva en el alcance revisado.
