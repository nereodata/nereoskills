**Veredicto:** RECHAZADO

Hades revisó el delta completo de pruebas de B-ADV-0039 mediante `--agente hades --prompt-file`. Informe transcrito de stdout. La reserva autorizada emitió el dictamen sobre el delta y los fixtures adjuntos. El error local `registered Core launch requires an installed app` impidió leer los archivos directamente y escribir el informe. El revisor contrastó los criterios textuales de la incidencia.

| Criterio | Puntuación |
|---|---:|
| Cobertura | 7/10 |
| Aserciones | 8/10 |
| Rojo correcto | 8/10 |
| Estabilidad | 9/10 |
| Media | 8/10 |

**Alta · Destino `artemisa`.** En `test_reserva_recuperada_no_propaga_cuota` se comprueban las entradas de Opus (2), Gemini (3) y GPT (5). Las filas de paso podrían duplicar esos consumos sin que falle la prueba. Comprobar que el conjunto de filas del principal conserva exactamente sus 11 tokens y excluye los consumos de los tres proveedores.

**Alcance.** Seis pruebas nuevas de FallosArnesTests, sus helpers y fixtures y el cambio en ReservaCuotaTests. Hades consideró cubierta la distinción de T2 entre conservar el vencimiento histórico y excluir la cuota vencida de las vigentes. Reconoció la cobertura de recuperaciones, correlación de invocaciones, revisión pendiente y commit parcial limpio.

**Evidencia.** 20 pruebas dirigidas, 18 verdes y dos fallos funcionales esperados. El resumen selecciona segundo cuando debe seleccionar primero y el bucle devuelve 0 cuando debe devolver 2. Diff-check limpio. Sin lint ni tipado configurados. Hades no ejecutó pruebas ni examinó producción.

El motor enrutó el hallazgo a Artemisa e indicó terminar el paso. La revisión de código anterior conserva C1 y C2 pendientes.
