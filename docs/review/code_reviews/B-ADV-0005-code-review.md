# Revisión de código: B-ADV-0005 (reevaluación)

**Veredicto: APROBADO**

**Fecha:** 2026-10-26 · **Modo:** orquestado, sin preguntas · **Revisor:** Hades

## Alcance

Se revisa todo el delta de producción `git diff c9dbdc7 --` sobre:
- `skills/orquestar/orquestar.py` y `skills/telegram_gateway/gateway.py`.
- `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`.
- `CHANGELOG.md`.

Se contrasta con el triaje y las decisiones del bug y con `docs/design/B-ADV-0005-design.md`, ya actualizado con HC-01, HC-02 y HC-03. Se ha leído el código de alrededor que el delta consume: `HARNESS`, `comando`, `configuraciones_con_cuota`, `consumo_cuotas` y `esperar`. No se revisan las pruebas (aprobadas con 9/10, regresión HC-01 incluida) ni la arquitectura.

## Análisis estático

Hay verificación en verde para este árbol, que no se ha relanzado:
- 98 pruebas de triaje.
- `py_compile` de `orquestar.py`, `gateway.py` y el test.
- `git diff --check`.

No hay linter ni tipado configurados. No hay secretos reales. No cambian dependencias ni manifiestos, así que la auditoría no aplica.

## Hallazgos anteriores

- **HC-01 (🟠): resuelto.** `cuota_descartada` (líneas 918-932) solo entra en juego cuando no hubo ninguna ejecución.
  - Toma los perfiles que el filtro omitió y busca su recuperación vigente en `consumo_cuotas`. Comprueba que su ejecutable exista, con `HARNESS[harness][0]` y `buscar_ejecutable`, y devuelve los segundos que faltan hasta la recuperación más temprana.
  - Si ese ejecutable tampoco existe, devuelve `None` y se mantiene el fallo «ningún arnés disponible», que es correcto.
  - **Agente:** registra una señal `sin_cuota` + `espera_s` con `modelos: {}` y devuelve 1. El bucle la recoge (búsqueda de `tipo == 'agente'` y `sin_cuota` en las filas nuevas) y espera.
  - **Paso:** pone `m = {'modelos': {}}` y sigue el camino de `esperar` que ya existía, con el tope de `--espera-max`.
  - Como `consumo_cuotas` no atribuye recuperación a filas sin modelo, la ventana original no cambia y ni la ausencia ni la señal generan cuota ni consumo.
  - Tras la espera, el perfil deja de estar filtrado y se vuelve a probar el principal.
- **HC-02 (🟡): resuelto.** Sin arneses, `agente()` imprime `[orquestar] <rol>: ningún arnés disponible…`, avisa con `error` y devuelve 1, sin prefijo `PARAR` ni `⏸`. En el paso se mantiene `parar()`, porque ahí sí se detiene el bucle.
- **HC-03 (🔵): resuelto.** Las dos señales agregadas del agente y la fila final del paso incluyen `escalado` cuando corresponde.
- **HC-04 (🔵):** sigue descartado.

## Comprobaciones pedidas, de nuevo sobre todo el delta

- **Cuota anterior con ausencias al final, sin duplicar consumo: correcto.**
  - Cuota dentro de la misma ejecución: `pendiente_cuota` o `ultima_cuota` emiten la señal agregada sin modelos ni tokens.
  - Cuota ya vigente al empezar: la cubre `cuota_descartada`.
  - En los dos casos, la recuperación sale solo de la fila original con `cuota_espera_s` y `modelo_cuota`.
- **Posición original:** se resuelve por identidad (`c is cfg_actual`) dentro de `configs_originales`. `configuraciones_con_cuota` filtra y conserva los mismos objetos, así que la búsqueda siempre encuentra el perfil y la posición coincide con el orden declarado.
- **Autenticación, red y `--cmd`:** sin cambios respecto a la revisión anterior. Los fallos que no son de cuota no prueban reservas en ningún consumidor, y `--cmd` aborta con `sys.exit`. Con `--harness`, el filtro no se aplica, no hay perfiles omitidos y se cae en el fallo claro.
- **Sesiones:** no pasan de un arnés a otro en el paso, el agente ni el gateway.

## Puntuaciones

| Criterio | Nota |
|---|---:|
| Corrección | 9 |
| Seguridad | 10 |
| Conformidad | 9 |
| Calidad | 8 |
| Eficiencia | 9 |
| Documentación | 9 |
| **Media** | **9** |

No hay hallazgos 🔴 ni 🟠.

## Hallazgos

### HC-05: 🔵 BAJA. `espera_s` de `cuota_descartada` es un `float`
- **Evidencia:** línea 930, `(hasta - instante).total_seconds()`. Se registra como `2700.0` en las métricas y se suma a `esperado`.
- **Consecuencia:** funciona porque `esperar` y las comparaciones aceptan `float`. Solo cambia el formato respecto a las demás filas, que son enteras.
- **Destino:** `descartar`. Opcionalmente, `math.ceil(...)` para no despertar un segundo antes.

### HC-06: 🔵 BAJA. Duplicación menor al registrar las dos señales agregadas del agente
- **Evidencia:** líneas 1362-1375. Son dos `registrar` casi idénticos.
- **Destino:** `descartar`. Es legible y está acotado.

### HC-07: 🔵 BAJA. `SKILL.md` no menciona el caso de cuota ya vigente
- **Evidencia:** el párrafo «Arnés ausente» de `skills/orquestar/SKILL.md` describe la conservación de la cuota cuando el intento disponible agotó «antes de las ausencias». No menciona el relanzamiento con la cuota ya vigente, que también espera el saldo restante.
- **Consecuencia:** el texto no queda falso, solo incompleto.
- **Destino:** `descartar`.

## Salida

El código queda aprobado y la corrección puede seguir a QA y documentación. Esta revisión solo actualiza el informe: no modifica producción, estados ni otras revisiones, y no hace commits.
