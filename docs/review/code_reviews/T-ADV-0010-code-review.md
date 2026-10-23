**Veredicto:** APROBADO

# Revisión de Código: T-ADV-0010 · Modelos de reserva ante agotamiento de cuota en pasos y subagentes

## Análisis Estático y Evidencias
- `git diff --check`: limpio (0 errores).
- `python -m unittest tests/test_orquestar.py`: verificado en verde con `adevv orquestar --verificar` sobre el árbol `be08f66c4f`.

## Puntuaciones
- **Corrección**: 9.5/10 — `lista_reservas()` normaliza objeto único o lista ordenada heredando `harness`, `model`, `effort` e `instructions` del rol base; `agente()` y `bucle()` recorren secuencialmente `[cfg_principal] + reservas` ante agotamiento de cuota (`espera_cuota`), registrando cada intento en `orquestar_metricas.jsonl`, reiniciando sesión si cambia el arnés y calculando `min(cuotas)` solo cuando todas las opciones se agotan.
- **Seguridad**: 10/10 — Sin vectores de inyección, secretos expuestos ni ejecución arbitraria fuera de los arneses validados.
- **Conformidad**: 10/10 — Fiel al triaje de `T-ADV-0010` y a todas las decisiones de diseño (`DEC-D01` a `DEC-D04` en `docs/design/T-ADV-0010-design.md`).
- **Calidad**: 9.5/10 — Código claro, compacto y consistente con el estilo de `skills/orquestar/orquestar.py`.
- **Eficiencia**: 9.5/10 — Conmutación inmediata en memoria sin sobrecoste cuando no hay error de cuota.
- **Documentación**: 9.5/10 — `skills/orquestar/SKILL.md` actualizado en las secciones **Roles** y **Sin cuota**, más docstring en `lista_reservas()`.

**Media:** 9.67/10

## Hallazgos
- **H-01 (🔵 BAJA · `descartar`)** — `skills/orquestar/SKILL.md:67`: errata menor de concordancia verbal («el bucle conmute inmediatamente» → «conmuta»). Cosmética; no afecta a la claridad de la instrucción.
- **H-02 (🔵 BAJA · `descartar`)** — `skills/orquestar/orquestar.py:1030`: `return codigo` final tras el bucle `for` en `agente()` es inalcanzable porque `configs_a_probar` contiene siempre al menos un elemento y todas las ramas retornan dentro del bucle. Inocuo como salvaguarda defensiva.
