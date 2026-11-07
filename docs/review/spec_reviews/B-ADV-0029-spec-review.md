**Veredicto:** APROBADO

# B-ADV-0029 · Revisión de especificación

Fecha: 2026-11-07. Alcance: los tres escenarios nuevos `@B-ADV-0029` de `skills/orquestar/features/orquestacion.feature`, frente al reporte y a la decisión de alcance del bug. Revisión aislada, sin inspección de diseño ni código de producción.

## Obligatorias

- ✅ No regresión: el delta solo añade escenarios; no elimina ni altera los existentes.
- ✅ Coherencia: el bug declara expresamente la nueva precedencia de `--harness` para el principal de cada paso y preserva el arnés explícito de las reservas. La documentación anterior de forzado global queda identificada como contrato que debe actualizarse en el mismo delta.
- ✅ Trazabilidad: las etiquetas `@B-ADV-0029` identifican el bug; no se añaden etiquetas `@CA-*` inexistentes.
- ✅ Delta real: el caso con `--harness codex` discrimina la atribución del arnés de las reservas y la reutilización indebida de sesión. Se complementa con continuidad dentro de un mismo arnés y con un principal forzado diferente al configurado.

## Puntuaciones

| Criterio | Nota |
|---|---:|
| Claridad | 9 |
| Completitud | 9 |
| Testeabilidad | 9 |
| Estructura | 9 |
| Media | 9 |

Los resultados observables incluyen comandos realmente lanzados, modelo y esfuerzo, sesión, métricas y continuación sin espera. El esquema cubre el alias histórico `development` y el rol vigente `artemisa`. La reproducción deberá demostrar el rojo por el comportamiento descrito, sin invocar servicios reales.

Sin hallazgos críticos o altos ni deuda nueva.
