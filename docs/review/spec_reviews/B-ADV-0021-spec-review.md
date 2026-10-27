**Veredicto:** APROBADO

# Revisión de especificación — B-ADV-0021 (segunda ronda)

**Media: 9/10.** Sin 🔴 ni 🟠. Los cinco hallazgos de la primera ronda están resueltos.

## Alcance y método

Reevaluación en modo orquestado (paso `especificar`, ID maestro B-ADV-0021). Hades aplica `/review-spec` de `~/.adevv/versions/0.6.1/`. Fecha: 2026-10-27.

Objeto: el `git diff` sin commitear en `release/v1.0` de:

- `F-03_actualizacion_automatica.md`: RF-F03-06, RF-F03-11, RF-F03-14, el caso límite y @CA-F03-17/18.
- `tests/features/actualizacion_automatica.feature`.
- `requirements.md`: R2 y la fila 8 de §4.
- `platform_plan.md`: §2, DEC-P02 y DEC-P13.
- `ciclo/trazabilidad.md`.
- El resumen de especificación del bug.

He revisado cada hallazgo anterior y el delta por si las correcciones rompían algo. He cotejado RF-F03-08, RF-F01-11, DEC-P10 y CA-F03-03/04/05/13. No he mirado diseño ni código, ni he ejecutado pruebas.

## Obligatorias

| Criterio | Resultado | Motivo |
|---|---|---|
| No regresión | ✅ | Solo se añaden escenarios. CA-F03-03 («la tomarán al terminar su paso actual»), CA-F03-04 (reinicio manual de motores anteriores), CA-F03-05 (recarga cooperativa del gateway) y CA-F03-13 (vuelta atrás compatible, 0.6.1 → 0.5.0) siguen siendo ciertos con el aviso condicionado. |
| Coherencia | ✅ | RF-F03-06, RF-F03-11, R2 y la fila 8 condicionan ahora la recarga como RF-F03-14. Que el proceso siga con su versión es lo que ya pedía RF-F03-08. DEC-P13 limita DEC-P10 de forma explícita. La limpieza se reintenta en el mismo punto que las copias de RF-F01-11, sin cambiar RF-F01-11. |
| Trazabilidad | ✅ | @CA-F03-17/18 están en los criterios de F-03 y en el resumen del bug, llevan `@B-ADV-0021` y figuran en `trazabilidad.md` (RF-F03-14 → CA-F03-17/18). Hay un detalle de etiqueta en el 🔵 H-06. |
| Delta real | ✅ | El comportamiento es nuevo y CA-F03-13 no lo duplica. |

## Puntuaciones

| Dimensión | Nota | Motivo |
|---|---|---|
| Claridad | 9 | Las causas, los textos literales, el aviso único por versión activa y la conservación del PID son inequívocos. |
| Completitud | 9 | Cubre el bucle y el gateway hacia un motor anterior a 0.5, la incompatibilidad de opciones, el aviso de instalación en los dos casos, la recarga posterior hacia una versión compatible y el límite de los motores 0.5.0–0.6.1. |
| Testeabilidad | 9 | Las versiones, `--calidad`, los mensajes, `orquestar.pid`/`telegram.pid` y `--estado` son observables. |
| Estructura | 9 | Los escenarios están en el `.feature` de la funcionalidad, como copia exacta de F-03. |

**Media: (9 + 9 + 9 + 9) / 4 = 9.**

## Hallazgos anteriores

| Hallazgo | Estado | Comprobación |
|---|---|---|
| 🟠 H-01 · El aviso de instalación promete recarga a procesos con opciones no admitidas | resuelto | La fila 8, RF-F03-06/11 y R2 prometen la recarga solo «si admite sus opciones; si no, siguen con su versión y lo avisan (desde v1.0.0)». CA-F03-18 parte de `adevv actualizar 0.6.1` y comprueba ese texto literal. |
| 🟡 H-02 · Gateway hacia motor anterior a v0.5 sin escenario | resuelto | CA-F03-17 incluye el gateway: sigue con la 1.0.0, conserva `telegram.pid` y avisa una vez. |
| 🟡 H-03 · El aviso para destinos anteriores a v0.5 callaba que los motores 0.5.0–0.6.1 se detienen | resuelto | La fila 8 y CA-F03-17 advierten «los de v0.5.0 a v0.6.1 se detendrán…». El motivo del descarte se ha reescrito y es coherente con el límite declarado. |
| 🟡 H-04 · DEC-P13 decía que DEC-P10 «se conserva sin cambios» | resuelto | Ahora dice «se conserva, limitada a destinos compatibles». |
| 🔵 H-05 · Trazabilidad auxiliar | resuelto | Hay filas de RF-F03-06/11/14 y etiqueta `@B-ADV-0021`. La fila de RF-F03-06 actualiza además su texto, que estaba desfasado. |

H-07 de la revisión de arquitectura sigue resuelto: §2 y DEC-P02 remiten a DEC-P13, y DEC-P13 declara la limpieza diferida, cuándo se reintenta y su coste.

## Hallazgos nuevos

### 🔵 H-06 · CA-F03-18 lleva la etiqueta `@RF-F03-06` aunque es una vuelta atrás explícita
- **Destino:** resolver
- **Detalle:**
  - El escenario arranca con `adevv actualizar 0.6.1` desde 1.0.0. Eso es una versión dirigida y menor que la última, es decir, RF-F03-11. RF-F03-06 trata la «versión nueva elegible» de la comprobación automática.
  - El aviso que comprueba (fila 8) es común a ambos, así que el contrato no cambia; solo la etiqueta apunta al requisito que no toca.
- **Corrección:** etiquetar `@RF-F03-11`, o añadirla junto a la actual, y ajustar `trazabilidad.md`.

### 🔵 H-07 · El título de CA-F03-17 solo menciona el bucle
- **Destino:** descartar
- **Detalle:** el escenario ahora cubre también el gateway («…con un bucle y un gateway en marcha»). Es solo cosmético.
