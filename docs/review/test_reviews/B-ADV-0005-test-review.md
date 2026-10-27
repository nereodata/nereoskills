# Revisión de pruebas: B-ADV-0005 (reevaluación 3: regresión HC-01)

**Veredicto: APROBADO**

**Fecha:** 2026-10-26 · **Modo:** orquestado, sin preguntas · **Revisor:** Hades

## Alcance y evidencia

Se revisa solo lo que se ha añadido a `skills/orquestar/test_arnes_ausente.py`: `test_cuota_vigente_y_reserva_ausente_conservan_espera`, la regresión que pidió la revisión de código (HC-01). Se contrasta con el feature, con el bug y con la DEC del triaje («ausencia no equivale a cuota; se conserva la señal de cuota aunque la última reserva falte»). No se han leído ni la producción ni el diseño. Las ocho pruebas anteriores ya estaban aprobadas (reevaluación 2) y no han cambiado.

Se reutiliza la evidencia y no se repite:
- Compilación del test: en verde.
- Rojo final en `docs/review/test_reviews/B-ADV-0005-red.md`, «Regresión HC-01», con `--verificar` y antes de corregir HC-01: 9 pruebas y 2 fallos. El agente no registra ninguna señal `sin_cuota` (0 frente a 1) y el paso no llama a `esperar(root, 2700)`. El resto está en verde.

Los dos fallos son justo el defecto de HC-01, no la sintaxis ni un fixture. No se ha ejecutado la suite completa. No hay linter ni tipado configurados.

## Regresión HC-01

- **Preparación:** cada flujo empieza con el registro vacío y una sola fila previa de cuota de `claude/principal`: `fecha 17:00Z`, `cuota_espera_s 3600`, `modelos: {}`. El reloj está fijado a `17:15Z` y `codex` (la reserva) está ausente. Es el caso de relanzar el bucle, o de invocar a Hades por segunda vez, con la cuota ya vigente.
- **Agente:** devuelve un código distinto de cero y registra exactamente una señal `sin_cuota` con `espera_s == 2700` y `modelos == {}`. No hay aviso `error`.
- **Paso:** devuelve un código distinto de cero, llama a `esperar(root, 2700)` una sola vez y no hay aviso `error`. Así no puede pasar ni un `parar('error', …)` ni una espera de 3600 recalculada.
- **Común a los dos:** la recuperación de `claude/principal` sigue siendo exactamente las `18:00Z` y no aparece cuota para `codex/reserva`. Hay una sola fila de ausencia, la de `codex`, sin `cuota_espera_s` ni `espera_s`. `lanzar` no se llama nunca, así que el principal agotado no se vuelve a ejecutar.

La prueba discrimina: una implementación que siga diciendo «ningún arnés disponible», o que reejecute al principal, o que atribuya cuota a la ausencia, falla.

## Puntuaciones

| Criterio | Nota | Justificación |
|---|---:|---|
| Cobertura | 9 | Toda la spec, más la regresión HC-01 en agente y paso. El gateway queda fuera porque no gestiona cuota (diseño de T-ADV-0026). |
| Aserciones | 9 | La espera restante es exacta, la señal es única y sin modelo, no hay error, la recuperación original se conserva y no hay lanzamientos. |
| Rojo correcto | 9 | Los dos fallos previos a la corrección son el defecto de HC-01. |
| Estabilidad | 9 | Instantes fijados con zona horaria, métricas reiniciadas en cada flujo, y procesos, esperas y avisos simulados. |

**Media: 9.** No hay hallazgos 🔴 ni 🟠.

## Hallazgos

### HT-09: 🔵 BAJA. La fila de ausencia de la regresión no comprueba posición ni consumo cero
- **Evidencia:** solo se comprueba `arnes == 'codex'` y que no tenga `cuota_espera_s` ni `espera_s`.
- **Consecuencia:** la posición y el consumo nulo ya los exigen otras pruebas en el mismo camino de registro. Además, la posición tras el filtrado por cuota no la fija el contrato.
- **Destino:** `descartar`.

Los hallazgos anteriores (HT-03, HT-06 y HT-07) siguen resueltos, y HT-05 y HT-08 siguen descartados.

## Salida

Las pruebas quedan aprobadas, incluida la regresión HC-01, y la corrección del código puede seguir. Esta revisión solo actualiza el informe: no modifica pruebas ni estados, y no hace commits.
