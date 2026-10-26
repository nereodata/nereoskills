# Revisión de pruebas — B-ADV-0005

**Veredicto: RECHAZADO**

**Para:** desarrollador.

**Fecha:** 2026-10-26.

**Modo:** orquestado, sin preguntas.

## Alcance y evidencia

Se revisa únicamente `skills/orquestar/test_arnes_ausente.py`, incluida su preparación de estados, frente a `skills/orquestar/features/orquestacion.feature` y el triaje y las decisiones del bug B-ADV-0005. Se aplican Hades y `/review-test` del almacén activo 0.6.0, ignorando el modelo del frontmatter. No se inspeccionan producción, diseño ni otras pruebas.

Se reutilizan `docs/review/test_reviews/B-ADV-0005-red.md` y las entradas de `orquestar_evidencias.jsonl`: para el árbol `0fc0a0f64da0461559faad519433f55dd0d39f08` constan `py_compile` verde y ejecución del test nuevo con código 1, a las 18:03:12 y 18:03:13 respectivamente. El informe rojo declara ocho pruebas, dos fallos y nueve errores por ausencias no recuperadas y evento inexistente. El registro confirma el código de salida, aunque no conserva los detalles de cada fallo. No se repiten esas verificaciones ni se ejecuta la suite completa. No hay linter ni tipado configurados, según la invocación.

El fixture del error operacional del paso utiliza `bucle(progreso=False)`: mantiene la firma sin cambios y evita simular progreso cuando la ejecución falla. No se objeta esa corrección.

## Puntuaciones

| Criterio | Puntuación | Justificación |
|---|---:|---|
| Cobertura | 7/10 | Cubre los tres consumidores, salto directo, cadena intermedia, agotamiento total, cuota previa, autenticación y filtrado. Falta exigir las métricas de ausencia comprometidas para el caso de cuota previa. |
| Aserciones | 7/10 | Hay comprobaciones concretas de reservas, sesiones, consumo y recuperación. El bucle sobre métricas ausentes del caso de cuota puede no comprobar ninguna fila; los avisos de la cadena solo se cuentan. |
| Rojo correcto | 9/10 | La evidencia suministrada atribuye el rojo a los comportamientos que se pretenden corregir; sintaxis verificada y fixture operacional ajustado. El rojo previo no acredita las aserciones posteriores a las excepciones. |
| Estabilidad | 9/10 | Directorio temporal por prueba, entorno aislado, instante fijado y procesos, esperas y red simulados. |

**Media: 8/10.** No supera el umbral estricto de 8 y existe un hallazgo alto.

## Hallazgos

### HT-01 — 🟠 ALTA — El caso de cuota previa no exige evidencia de la reserva ausente

- **Evidencia:** `skills/orquestar/test_arnes_ausente.py:171-191`. Se comprueban las filas de cuota de agente y paso y la recuperación agregada del principal. Después, solo se valida `sin_cuota` y la ausencia de `cuota_espera_s` dentro de un `if fila.get('arnes_ausente')`. No se exige que exista ninguna fila de ausencia, ni se comprueban su flujo, posición, arnés, modelo o consumo cero.
- **Contrato:** el esquema «Cuota en un arnés disponible y última reserva ausente» exige identificar ese intento y registrar cero en todos sus contadores y coste. H-02 y DEC-ESP-02 rechazan expresamente métricas sin atribución suficiente.
- **Consecuencia:** una corrección que conserve la cuota del principal pero omita por completo las métricas de la reserva ausente en este camino pasaría el caso. También podrían pasar filas atribuidas al flujo o modelo equivocado, o con consumo indebido. Los casos sin cuota previa no discriminan esta omisión específica.
- **Para:** desarrollador.
- **Destino:** resolver en las pruebas de B-ADV-0005 antes de aprobarlas.
- **Corrección necesaria:** exigir, para agente y paso, las filas de ausencia de la última reserva con identidad completa y consumo cero, y comprobar en ellas la ausencia de cuota y recuperación. Las comprobaciones deben fallar si faltan esas filas. Puede mantenerse la configuración de arneses equivalente que usa la prueba; no es necesario copiar literalmente los nombres del feature.

### HT-02 — 🟡 MEDIA — Dos avisos no garantizan uno por cada configuración ausente

- **Evidencia:** `skills/orquestar/test_arnes_ausente.py:166` exige dos llamadas del evento `arnes`, pero no examina su mensaje. El helper `comprobar_ausente`, en el salto directo, también comprueba únicamente la existencia del evento. La identificación del arnés solo se verifica en consola.
- **Contrato:** H-01 exige un aviso propio por cada configuración ausente; el feature requiere uno por codex y otro por claude en la cadena y que el aviso del salto directo identifique el arnés.
- **Consecuencia:** dos avisos que identifiquen ambos codex, o mensajes genéricos sin identificación, satisfacen las aserciones aunque la notificación incumpla el contrato.
- **Para:** desarrollador.
- **Destino:** resolver en el mismo archivo de pruebas.
- **Corrección necesaria:** comprobar el contenido de los avisos `arnes`: cada ausencia debe corresponder a su arnés en el flujo probado, sin duplicar uno y omitir otro. Verificar también la identificación en el salto directo; no hace falta fijar toda la redacción del mensaje.

## Salida

Devolver al desarrollador para resolver HT-01 y HT-02 y solicitar nueva revisión. No se requiere intervención humana ni cambio de especificación. Esta revisión solo crea el informe; no modifica pruebas, producción, estados ni realiza commits.
