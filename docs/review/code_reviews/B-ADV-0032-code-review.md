**Veredicto:** RECHAZADO

# Revisión de código — B-ADV-0032

## Alcance y método

Revisión independiente del delta de `314f3d8df8660f4057e2723a41f9c992e76c0c05` respecto a `9a143486c663f2afe2bbe4e7ef3a30743c65532a`, contrastado con el código vigente adjunto. Alcance limitado a captura JSON, terminación de procesos, timeout, stdin de `agy` y propagación en sus llamantes.

Se han considerado la ficha del bug, su diseño y el plan de plataforma facilitados. Quedan excluidos B-ADV-0033, las pruebas como código de producción y las distribuciones `dist/`.

Revisión realizada exclusivamente sobre los materiales adjuntos, sin herramientas ni acceso a disco. Las verificaciones siguientes son evidencia aportada por el invocador para el árbol `c5f35c016a`, sin cambios de código posteriores.

## Análisis estático y verificación

| Comprobación | Resultado y procedencia |
|---|---|
| Regresión autorizada | `adevv orquestar --verificar "python -m unittest tests.test_orquestar.SubprocesoColgadoTests"`: 3 pruebas OK, 0,919 s, código 0. Evidencia reutilizada. |
| Integridad del diff | `git diff --check 9a143486c663f2afe2bbe4e7ef3a30743c65532a`, mediante `--verificar`: código 0. Evidencia reutilizada. |
| Formato y lint | `adevv orquestar --calidad --base 9a143486c663f2afe2bbe4e7ef3a30743c65532a`: código 0, pero ambas etapas **OMITIDAS** por ausencia de herramientas configuradas. No equivalen a comprobaciones aprobadas. |
| Tipado | Omitido justificadamente: no hay herramientas configuradas. |
| Dependencias | Auditoría no aplicable: no cambian dependencias en el alcance. |
| Seguridad | Inspección manual del material: no se observan credenciales expuestas ni interpolación de comandos mediante shell en el delta revisado. No consta un escáner de seguridad ejecutado. |

No se han repetido verificaciones ni ejecutado otros grupos de pruebas.

## Puntuaciones

| Criterio | Puntuación | Razón |
|---|---:|---|
| Corrección | 6/10 | Corrige stdin y captura concurrente, pero no garantiza la terminación del árbol en POSIX. |
| Seguridad | 9/10 | Invocaciones mediante argumentos y sin nuevas dependencias; no se observan secretos. |
| Conformidad | 7/10 | Mantiene el motor y el stack establecidos; el cierre de descendientes exigido por el bug y el diseño queda incompleto. |
| Calidad | 8/10 | Funciones separadas y contratos de retorno conservados; falta validar valores no finitos del timeout. |
| Eficiencia | 8/10 | Sondeo y esperas explícitamente acotados; los descendientes pueden sobrevivir al cierre. |
| Documentación | 8/10 | Explica el mecanismo, pero afirma una terminación del árbol que la implementación POSIX no realiza. |

**Media: 7,67/10.** Existe un hallazgo de gravedad alta; no procede aprobar.

## Hallazgos

### H-01 — 🟠 ALTA: en POSIX se termina únicamente el proceso directo

- **Para:** desarrollador
- **Destino:** resolver
- **Ubicación:** `skills/orquestar/orquestar.py`, líneas 1666–1687 y 1736–1743; llamadas desde 1800–1807.
- **Evidencia:** `_terminar_arbol_proceso()` utiliza `taskkill /T` exclusivamente en Windows. En POSIX ejecuta solo `p.kill()` y `p.wait()`. El `Popen` tampoco establece una sesión o grupo independiente que permita terminar conjuntamente al arnés y sus descendientes.
- **Caso concreto:** `agy` crea un hijo que hereda stdout o stderr y permanece vivo. Al vencer el timeout o la gracia posterior al JSON, se mata al proceso directo, pero el hijo continúa ejecutándose y conserva los descriptores heredados.
- **Impacto:** incumple la terminación del árbol requerida para B-ADV-0032. Aunque la ruta JSON limita la espera de los lectores y puede devolver el control, deja trabajo del arnés activo: ese descendiente puede seguir consumiendo recursos o modificando artefactos después de que el invocador haya registrado el cierre.
- **Corrección requerida:** establecer y terminar una unidad de procesos aislada en POSIX, sin alcanzar al orquestador, con espera acotada. Mantener el resultado JSON y sus métricas cuando corresponda.
- **Validación requerida:** incorporar al grupo de regresión autorizado un caso con descendiente real que herede un pipe y comprobar que no sobrevive al timeout o al cierre forzado. El verde aportado no acredita expresamente esta condición.

### H-02 — 🟡 MEDIA: valores no finitos pueden eliminar el límite de espera

- **Para:** desarrollador
- **Destino:** resolver
- **Ubicación:** `skills/orquestar/orquestar.py`, líneas 1690–1703.
- **Evidencia:** `float(val)` acepta valores como `"inf"` y `"nan"`. El primero supera `num > 0` y se devuelve como timeout infinito; el segundo devuelve `None`. Ambos evitan el valor por defecto de 1800 segundos de `agente()`.
- **Caso concreto:** con `ORQUESTAR_TIMEOUT_AGENTE_S=inf` y un arnés que no emite JSON final, la comparación de vencimiento nunca se cumple. Con `nan`, y sin otro timeout general, queda desactivada.
- **Impacto:** una configuración inválida vuelve a permitir la espera indefinida que este bug pretende acotar.
- **Corrección requerida:** comprobar que el número sea finito antes de aceptarlo y aplicar el tratamiento de configuración inválida ya existente. Definir por separado cualquier desactivación intencionada mediante valores no positivos.

## Aspectos conformes

`agente()` pasa `entrada=None` a `agy` tanto en la primera invocación como en el reintento, y la captura JSON lo traduce a `stdin=subprocess.DEVNULL`. Los dos streams se leen concurrentemente y los llamantes evitan reiniciar una sesión como nueva cuando las métricas indican timeout.

La implementación permanece en el motor existente y utiliza la biblioteca estándar, de acuerdo con el plan de plataforma. No se identifica una desviación arquitectónica que requiera una nueva DEC.

El reporte queda preparado para que Artemisa enrute los hallazgos a desarrollo y solicite su reevaluación.
