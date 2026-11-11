# Dictamen vigente — B-ADV-0034

**Veredicto: APROBADO** · **Media: 8,75/10**.
Última revisión de Hades: delta HC-01/HC-02, árbol `8d518bf38b`.
Tres pruebas nuevas y dos reforzadas aprobadas: reserva visible del PID antes
de segunda respuesta, fallo spawn sin residuo, aceptación y limpieza del PID
propio; avisos de parada/dependencia no dicen reanudada y sí incorporada.
Evidencia recibida: py_compile verde; red 13 tests, 2 fallos de aviso y 2 errores
de PID, sin errores de carga. PID de doble spawn simulado es el del test vivo,
no se crea bucle. Captura de funciones reales antes de parchear, Popen permite
operaciones Git auxiliares. Aserciones sobre comportamiento, no por construcción.
HT-01/02/03 resueltos, sin hallazgos nuevos. Puntuaciones 9/9/9/8; conserva
aprobación previa. Sin acceso al disco, sin ejecutar pruebas ni revisar código.
HC-01/02 siguen sujetos a reevaluación de código.

## Historial de revisiones

# Revisión de pruebas — B-ADV-0034

**Veredicto: RECHAZADO**
**Media: 7,75/10**
**Fecha:** 2026-11-11

Hades mediante --agente hades; transcripción de su dictamen sobre adjuntos.
Sin acceso al disco por registered Core launch requires an installed app;
no se ejecutaron pruebas ni se revisaron producción o diseño.
Alcance: diez pruebas nuevas, fixtures, aislamiento, aserciones y limpieza,
frente a BDD @B-ADV-0034, CA y DEC-ESP-0034-01.
Evidencia recibida: rojo por --responder ausente, py_compile verde;
formato y lint omitidos. Cleanup y UTF8 posteriores a primera evidencia.

| Dimensión | Nota | Motivo |
|---|---|---|
| Cobertura | 8 | Casos principales, sin garantizar contención concurrente. |
| Aserciones | 8 | Persistencia, estados, diagnósticos, archivos y lanzamientos; incorporación única parcial. |
| Rojo correcto | 9 | Interfaz ausente, sin fallo de carga. |
| Estabilidad | 6 | Dependencia del planificador y entorno heredado en hijos. |

## HT-01 — 🟠 ALTA — Concurrencia sin contención garantizada

**Para:** desarrollador.
Crear dos Popen consecutivos permite que el primero termine antes de que el
segundo entre. Una duplicada y una sola entrada también resultan de entregas
secuenciales; no discrimina persistencia insegura entre escritores.
Introducir coordinación controlada, esperas acotadas y limpieza garantizada;
comprobar terminación, una recepción y registro íntegro, detectando pérdida de
exclusión entre escritores. Corregir antes de aprobar.

## HT-02 — 🟡 MEDIA — Entorno Telegram de hijos no explícitamente aislado

**Destino:** resolver. **Responsable:** desarrollador.
Parches del padre no se propagan a intérpretes nuevos; pasar entorno controlado
sin credenciales y garantizar aislamiento con mecanismo de pruebas disponible.

## HT-03 — 🟡 MEDIA — Incorporación única sin comprobar contexto

**Destino:** resolver. **Responsable:** desarrollador.
Contar resultados y HEAD estable no detecta una primera incorporación que
escriba dos veces. Comprobar contenido persistido, decisión una sola vez y
contexto idéntico tras segunda incorporación.

Reevaluar delta de pruebas y evidencia dirigida; no suite completa.

## Reevaluación de Hades · 2026-11-11

**Veredicto: APROBADO** · **Media: 8,75/10**.
Árbol identificado por Hades: `027a356d73`. Revisión limitada a HT-01/02/03
y delta corrector sobre adjuntos; sin producción, diseño ni ejecuciones.
Disco sigue inaccesible. Evidencia aceptada: py_compile verde y red actualizado
10 tests, 15 fallos y 2 errores por --responder ausente; no fallos de carga.

| Hallazgo | Resultado | Evidencia |
|---|---|---|
| HT-01 | resuelto | Primer hijo retenido dentro del bloqueo; segundo anuncia intento; espera negativa acotada antes de liberar; terminación, deduplicación y otra raíz intacta. |
| HT-02 | resuelto | Intérpretes hijos reciben entorno sin TELEGRAM_* y UTF8; protección importada en padre. |
| HT-03 | resuelto | Decisión aparece una sola vez; contexto idéntico y HEAD estable tras segunda incorporación. |

Puntuaciones: cobertura 9, aserciones 9, rojo correcto 9, estabilidad 8.
Estabilidad mantiene dependencia temporal limitada de la observación negativa,
con coordinación explícita, límites y cleanup finally.
Sin hallazgos nuevos ni críticos/altos abiertos. La aprobación evalúa pruebas;
no acredita implementación funcional.

## Reevaluación final de fixture · Hades

**APROBADO**, 8,75/10, árbol `0d6cdba719`. Hades reconoce que la aprobación
previa no detectó consultar argv reemplazado. Capturar canal antes y usarlo en
ambas condiciones resuelve el defecto, preserva exclusión y cleanup.
HT-01/02/03 resueltos, sin nuevos. Acepta evidencia dirigida de 35 tests OK,
concurrencia 1 OK, py_compile y diff-check verdes sin repetirla.
Puntuaciones 9/9/9/8. Sin acceso al disco, informe devuelto y transcrito.

## Continuidad de reserva PID · última revisión de Hades

**Veredicto: APROBADO**, media global 8,75, árbol `66d6518c6c`.
Alcance solo refuerzo de test_hijo_acepta_titularidad_pid_publicada_por_padre;
resto aprobado vigente. Reserva real PID propio y observadores Path.unlink y
write_text detectan eliminación/republicación antes de bucle, delegando demás
operaciones. Comprueba PID al entrar y permite limpieza final.
Discrimina HC-01 sin depender de intercalación temporal. Acepta red
AssertionError reserva desaparece en main y compilación verde sin repetir.
Delta 9/9/9/9, sin nuevos, HT-01/02/03 resueltos. Disco inaccesible, sin ejecutar
comandos, sin producción/diseño; HC-01 pendiente de review-code.
