**Veredicto:** RECHAZADO

# Revisión de código — B-ADV-0037

Hades `/review-code`, modo orquestado, siguiendo el perfil y la skill adjuntos. Revisión estática del delta completo de producción y documentación frente al triaje, diseño y plan de plataforma. No se revisa la implementación de pruebas.

No se pudo guardar `docs/review/code_reviews/B-ADV-0037-code-review.md`: falló la escritura local. Este informe completo constituye el respaldo solicitado. No se modificaron producción, backlog ni commits.

## Análisis estático y evidencia

Se acepta la evidencia del árbol `656dbf2cada563c0acee44a3c971c83a5ba2f857`: 71 pruebas dirigidas OK, compilación del delta y `git diff --check` verdes mediante `--verificar`. No se repitieron esos comandos ni se ejecutó la suite completa. Sus resultados no sustituyen la revisión de código.

Se intentó ejecutar:

```text
adevv orquestar --calidad --base c29d8c67bdbdc8d587e78faf2dd2025007113ea8
```

El proceso no arrancó: `registered Core launch requires an installed app`. No se utilizó `--aplicar`. Se registra la evidencia aportada de omisión de formato/lint por ausencia de herramientas; no equivale a herramientas ejecutadas en verde. Sin tipado ni escáner de secretos configurados y sin cambios de dependencias.

El análisis se limita a los materiales adjuntos; no se acredita contraste independiente con el árbol. `dist/` queda fuera.

## Puntuaciones

| Dimensión | Nota | Motivo |
|---|---:|---|
| Corrección | 6/10 | El cierre operativo de hotfix conserva una reconstrucción incorrecta de rama. |
| Seguridad | 9/10 | El veto precede a las consultas remotas; no se identifican nuevas inyecciones ni credenciales expuestas en el delta. |
| Conformidad | 7/10 | La regla compartida sigue el diseño, pero quedan consumidores de cierre sin adaptar al parche y la rama hotfix. |
| Calidad | 8/10 | Centralización clara; propagación incompleta del contrato de versión. |
| Eficiencia | 9/10 | La acreditación de informes no invoca modelos ni consulta la red. |
| Documentación | 8/10 | Describe el veto y recuperación; el flujo de hotfix anunciado queda limitado por RC-01. |

**Media: 7,83/10. Existe un hallazgo de severidad ALTA.**

## Hallazgos

### RC-01 — El cierre del bucle intenta una rama release al terminar una hotfix

- **Severidad:** 🟠 ALTA.
- **Para:** desarrollador/artemisa.
- **Destino:** resolver.
- **Ubicación:** `skills/orquestar/orquestar.py::bucle`, bloque `cierre_de_version(e)` y asignación de `rama_cierre`.

Cuando `estado()` devuelve `PARAR` con `Versión v1.1.2 terminada.`, el bucle reconstruye:

```python
rama_cierre = e[3] if e[0] == 'PASO' else f'release/{version}'
```

El selector recorre correctamente `hotfix/v*`, pero pierde la rama concreta al devolver ese estado `PARAR`.

**Caso concreto:** solo existe `hotfix/v1.1.2`, todos sus maestros están cerrados y revisados y ya existe la revisión de arquitectura. El selector devuelve `PARAR`. Con `validation.command` configurado, el bucle intenta cambiar a `release/v1.1.2` antes de verificar la suite. Si esa rama no existe, termina con `no puedo cambiar a release/v1.1.2`, sin alcanzar la parada normal de versión ni su aviso. Si existe una rama release distinta, puede comprobar esa rama en lugar de la hotfix seleccionada.

**Corrección requerida:** conservar o resolver la rama concreta seleccionada también cuando el cierre se expresa como `PARAR`; no reconstruir su prefijo únicamente desde la versión. Aportar validación dirigida con arquitectura ya presente y solo hotfix abierta. No requiere cambiar la especificación.

### RC-02 — Los avisos de cierre con parche omiten el resumen de Telegram

- **Severidad:** 🟡 MEDIA.
- **Para:** desarrollador/artemisa.
- **Destino:** resolver.
- **Ubicación:** `skills/orquestar/orquestar.py::avisar`.

La extracción de versión sigue utilizando:

```python
re.search(r'Versión (v\d+\.\d+) terminada\.', texto)
```

`Versión v1.1.2 terminada.` no coincide: el patrón espera un espacio después del menor. Por ello no se llama a `cargar_cierre_version().resumen`, aunque el cierre ya admite parches completos.

**Efecto:** el aviso pierde el resumen de tareas, bloqueos, validaciones funcionales y orden de confirmación que se adjunta para versiones sin parche.

**Corrección requerida:** reconocer y conservar el parche opcional completo al extraer la versión y solicitar su resumen, manteniendo el comportamiento histórico de `vX.Y`.

## Resto del delta

La ruta canónica por ID elimina la aceptación por prefijos parecidos. El primer veredicto reconocido decide y N/A exige un motivo de ausencia de código. Los tres puntos de entrada reutilizan `pendientes_cierre`; la API vuelve a validar en el worktree integrado. Emitir un informe no etiqueta ni publica por sí solo.

La identidad operativa completa separa parches y mantiene la equivalencia del parche cero. Las métricas conservan su agrupación mayor/menor. Las rutas de intervención y bloqueo incorporan `nombre_version`.

No se identifica una desviación arquitectónica que requiera una DEC adicional en el plan de plataforma. CA3 se acepta conforme al expediente aportado de los informes formales RECHAZADO de B-ADV-0032/33; sus correcciones permanecen fuera de este bug.

## Resolución

Resolver RC-01 y RC-02 y reevaluar el delta con validación dirigida. No se solicita suite completa ni intervención humana.

Las aprobaciones previas de especificación y pruebas se mantienen. Este rechazo corresponde al delta de producción y documentación. No se publica ni etiqueta la versión.
