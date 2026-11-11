**Veredicto:** RECHAZADO · **7,50/10**

# B-ADV-0044 · Revisión independiente de pruebas

Rama `hotfix/v1.1.3`. Base `4fc39ce8a27b4f2ee6b1af1598ab0760b564cfd5`. Árbol acreditado `68247f62b598e7f1ec3fd6c5e63eaed4208fff89`.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 7/10 | Los seis escenarios tienen pruebas identificables. Quedan sin discriminar la autorización del proveedor tras la recarga y la espera efectiva por cuota. |
| Aserciones | 7/10 | Las secuencias exactas de invocaciones, los commits limpios y los consumos separados detectan regresiones. En la rama de cuota basta con registrar el bloqueo y emitir un aviso. |
| Rojo correcto | 9/10 | Los doce fallos aportados son discrepancias de comportamiento. El incidente produce cinco invocaciones frente a dos y la aprobación antigua permite pasar prematuramente a revisar la versión. |
| Estabilidad | 7/10 | El repositorio temporal aísla el trabajo y las esperas están simuladas. El nuevo módulo hereda el entorno del proceso y la configuración externa de Git al crear commits. |

## Contraste con los seis escenarios aprobados

| Escenario | Qué demuestra el delta |
|---|---|
| 1. Diagnósticos en desarrollo y análisis | Las tres filas entran por el bucle, crean commits con árbol limpio y exigen exactamente dos llamadas. Comprueban el aviso con paso e ID, los consumos del paso y la ausencia de pregunta. La simulación de Hades y la variación de las notas tienen los límites de H1 y H3. |
| 2. Presupuesto de `work-plan` | Elimina el plan, crea un commit vacío y después modifica el seguimiento. Exige dos llamadas a `work-plan` y un aviso que identifica el paso. La ejecución aportada hizo cinco llamadas. |
| 3. Avance parcial en ficha antigua | El WIP corrige `doble` y la prueba confirmada exige `doble(3) == 6`. Ambas aportaciones, el escenario y el dictamen deben producir la secuencia de progreso `[False, True, False, False]` y conservar la ficha en curso. La quinta variante verifica la respuesta incorporada y las tres llamadas esperadas al resolverla entre pasos. |
| 4. Alternancia, recarga y reinicio | La prueba transfiere el estado serializado y exige A, B, A antes del arranque manual. Después comprueba las cinco marcas de progreso acumuladas y el WIP de B. En el rojo hubo dos llamadas adicionales a A antes del arranque manual. La autorización del segundo proveedor queda abierta en H1. |
| 5. Retorno erróneo y cierre revisado | Las tres filas confirman el mismo cambio de producto y devuelven código 1. El informe antiguo precede al cambio y el vigente se incorpora con él. Las expectativas distinguen reintento con espera y paso a revisión de versión. El ajuste en `test_fallos_arnes.py` aporta ficha e informe a la regresión previa de cierre. |
| 6. Reserva y cuota | La prueba ejerce `motor.agente`, distingue los dos resultados de la reserva y verifica consumos 7 y 9 bajo una invocación común y 11 para el paso. El caso de éxito observa la continuación hasta el límite de pasos. H2 afecta a la rama de cuota. |

## Hallazgos

**H1 🟠 ALTA · Autorización del proveedor de Hades.** `test_alternancia_recarga_proveedor_y_reinicio_manual` configura la ficha con `codex/potente`, pero inserta directamente una fila de Hades con `arnes='agy'` tras la recarga. La preparación no declara esa reserva ni ejerce su selección. Además, `repeticion` toma el modelo de `ejecutar`, que corresponde al paso exterior. Un motor que respete el modelo exterior y omita el perfil de Hades podría satisfacer esas aserciones. **para: desarrollador**. Declarar los perfiles autorizados del revisor en el caso y observar qué arnés y modelo recibe el lanzamiento simulado. Conservar el límite de dos intentos de A al cambiar entre esos perfiles y comprobar que no interviene un tercero.

**H2 🟠 ALTA · La espera por cuota puede perderse aunque la prueba pase.** En `reserva(True)`, `espera_max=0`, `max_pasos=1` y se descarta el retorno de `bucle`. Las aserciones aceptan que el motor registre `bloqueo_agente`, avise de la cuota y termine sin programar una espera, incluso cuando una espera estaría permitida. El caso previo de cuota con commit limpio también fija el máximo de espera en cero. **para: desarrollador**. Habilitar una espera que cubra la cuota simulada y observar una llamada a `esperar` asociada a la revisión o al perfil agotado. El doble puede devolver una parada cooperativa para verificar la salida y la ausencia de relanzamiento inmediato, sin esperar tiempo real. Conservar las aserciones de consumo.

**H3 🟡 MEDIA · Las notas solo varían en el número.** `notas` repite las mismas frases en ambos intentos y sustituye `n`. Un detector que normalice cifras y compare literalmente el último diagnóstico podría superar el caso y volver a contar como avance una reformulación del mismo impedimento. **Destino: resolver**. Usar dos redacciones distintas y dos fechas fijas para la misma falta de acceso. Conservar los dos commits limpios y el límite exacto de llamadas.

**H4 🟡 MEDIA · La comprobación del informe usa el ID del bug en la fila de tarea.** Tras crear `T-DEMO-0001`, `self.informe` sigue apuntando a `B-DEMO-0001-code-review.md`. Una aprobación espuria para la tarea pasaría inadvertida en esa aserción. **Destino: resolver**. Construir la ruta que se comprueba a partir del `iid` recibido por `repeticion`.

## Evidencia y límites

La ejecución dirigida aportada del 11 de noviembre de 2026 a las 17:47:27 registró 84 pruebas, 12 fallos de aserción y ningún error de carga. Los cuatro controles de avance que usan `avance` sí registraron el entregable como progreso en el rojo. Fallaron porque se permitió un intento adicional. Los mensajes de argumentos inválidos pertenecen a pruebas de la CLI.

Se acepta el `git diff --check` en verde del mismo árbol. Formato y lint se omitieron por ausencia de herramientas y el proyecto no declara comprobador de tipos. El dictamen se basa en el perfil de Hades, la skill, los criterios, las pruebas y la evidencia adjuntos. La lectura local falló con `registered Core launch requires an installed app` y el proceso Node alternativo también terminó al arrancar. No se repitieron verificaciones ni se inspeccionó la implementación.
