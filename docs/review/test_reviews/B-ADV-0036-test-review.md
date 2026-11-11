**Veredicto:** RECHAZADO

# B-ADV-0036 · Revisión de pruebas

Hades evaluó el delta de `SuiteRecoveryTests`, los escenarios y el diseño mediante la reserva autorizada de `--agente hades --prompt-file`. La lectura local del revisor falló con «registered Core launch requires an installed app». Este informe transcribe su dictamen sobre los adjuntos. Hades no ejecutó las pruebas ni pudo inspeccionar las fixtures que quedaban fuera del delta.

| Criterio | Puntuación |
|---|---:|
| Cobertura | 6/10 |
| Aserciones | 7/10 |
| Rojo correcto | 9/10 |
| Estabilidad | 8/10 |
| Media | 7,5/10 |

| Hallazgo | Destinatario | Corrección requerida |
|---|---|---|
| H1 · Alta | Desarrollador · resolver | Retomar el cierre con la misma evidencia tras el error operativo. Comprobar que se conserva la identidad de la solicitud, que el reintento obtiene un dictamen válido y que durante la espera no hay aviso de bloqueo humano. |
| H2 · Alta | Desarrollador · resolver | En ambos casos terminales, exigir `status: blocked` y comprobar los arreglos y evidencias del grupo, incluido el resultado del último arreglo. Consultar el planificador al retomar para demostrar que no ofrece otro intento. |
| H3 · Media | Desarrollador · resolver | Alinear estrategia y conclusión de la fixture. Una recaída por la columna ausente debe pedir una intervención relacionada con esa columna. La renovación de certificado pertenece al grupo de firma. |

El verificador ejecutó 19 pruebas dirigidas con cuatro fallos funcionales en 28,937 s. La compilación de las pruebas pasó. El proyecto omitió formato y lint por ausencia de herramientas y carece de tipador configurado. El rojo discrimina el comportamiento anterior en las rutas alcanzadas. Las aserciones posteriores a los primeros fallos quedan pendientes de ejecución.

Los tres hallazgos se enrutaron a Artemisa. La próxima revisión de pruebas debe incluir las fixtures completas y la evidencia dirigida de la corrección.
