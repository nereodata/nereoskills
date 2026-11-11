# B-ADV-0036 — Dictamen consolidado /review-spec

**Veredicto: RECHAZADO.**
**Destino del impedimento de la subfase A: especificador.**

El CA 8 completo subsana la omisión documental anterior. Persisten la contradicción con el contrato vigente y la falta de una definición observable de identidad causal y finitud. No se necesita intervención humana para resolver este impedimento.

## Alcance y evidencia

Reevaluación limitada al material subsanado y su efecto sobre F-01, F-02 y F-03. Incluye los ocho criterios completos y los cuatro escenarios/esquemas vigentes de B-ADV-0006. Los escenarios aprobados se consideran contratos de referencia; no se vuelve a evaluar su calidad.

No existe delta BDD ni evals nuevos. El dictamen clasifica el impedimento para generarlos; no aprueba una especificación todavía inexistente. No se revisan diseño, implementación ni pruebas.

Se reutiliza la evidencia aportada de la base:

```text
adevv orquestar --verificar "python -m unittest discover -s tests -p test_orquestar.py -k SuiteRecoveryTests"
Salida 0 · 16 pruebas · 21,747 s
```

Esta evidencia acredita la base verificada; no demuestra el cumplimiento del comportamiento solicitado. No se han ejecutado herramientas, repetido pruebas ni escrito archivos.

## Obligatorias

| Comprobación | Resultado |
|---|---|
| No regresión | ✅ No se han modificado ni eliminado escenarios. La compatibilidad del futuro delta sigue pendiente de la resolución contractual. |
| Coherencia | ❌ El contrato solicitado contradice la transición vigente `dificil/2` y cambia el significado de las recaídas al introducir grupos causales. |
| Trazabilidad | Pendiente: no existen etiquetas `@CA-*` del delta que contrastar. Los ocho criterios de origen están ahora completos. |
| Delta real | Pendiente: el cambio de comportamiento está identificado, pero aún no está expresado en escenarios o evals. |

## Puntuaciones

No procede asignar puntuaciones de claridad, completitud, testeabilidad y estructura a escenarios inexistentes. La media anterior de **6,75** valoraba provisionalmente el material preparatorio; **no se conserva como puntuación del delta BDD**.

El rechazo se sostiene por los hallazgos graves siguientes, con independencia de una media.

## Reevaluación de hallazgos

### 🔴 F-01 — Contradicción contractual: **persiste**

**Para: especificador.**

La fila `dificil/2` exige `blocked` y parada con aviso al alcanzar tres recaídas. Los CA 1, 2 y 5 exigen diagnóstico previo y permiten el bloqueo humano únicamente con destino `humano`, pregunta concreta y justificación.

El esquema vigente identifica el cierre por versión y comando, admitiendo salida distinta. Eso no distingue recaídas del mismo grupo causal de grupos nuevos, distinción exigida por el CA 6.

**Decisión requerida:** documentar la sustitución contractual autorizada y sus límites:

- Qué resultado sustituye el bloqueo automático de `dificil/2`.
- Cómo se restringe el cómputo de recaídas al grupo causal correspondiente.
- Qué comportamiento previo se conserva para bugs ya `blocked` o `cancelled`.
- Que un cierre de distinta versión o comando conserva su independencia y obtiene otro ID, salvo cambio expresamente justificado.

El escenario adicional «Un cierre diferente obtiene su propio bug» amplía las garantías que debe conservar la resolución; no elimina la contradicción.

**Alcance:** reconciliar el contrato antes de generar escenarios. No corresponde al desarrollador ni a Artemisa decidir qué expectativa aprobada deja de regir.

### 🟠 F-02 — Identidad causal, presupuesto y finitud: **persiste**

**Para: especificador.**

Los CA 2, 6 y 7 fijan la intención, pero no resuelven suficientemente cómo observar sus límites. El CA 8 completo exige regresiones de los tres destinos; no define esos límites.

**Decisión requerida:** precisar mediante ejemplos verificables:

- Cuándo una nueva ejecución constituye una recaída del mismo grupo y cuándo descubre otro grupo.
- Qué ocurre con el presupuesto al resolver un grupo y aparecer otro.
- A qué unidad se aplica «una única revisión diagnóstica».
- Qué sucede si, tras continuar con una estrategia revisada, persiste el mismo impedimento.
- Qué condición produce una salida terminal y evita reabrir indefinidamente su diagnóstico.

**Alcance:** resultados observables y casos límite. No se exige una representación interna, un algoritmo concreto ni un límite numérico inventado por el revisor.

### F-03 — Material incompleto y ausencia de delta: **resuelto parcialmente; retirado como hallazgo alto autónomo**

**Responsable del trabajo pendiente: especificador.**

**Resuelto:** el CA 8 está íntegro. Exige regresiones deterministas para `desarrollador`, `especificador` y `humano`, y demostrar que el contador por sí solo no bloquea al humano.

**Pendiente:** producir el delta BDD/evals y verificar su trazabilidad y cobertura.

La ausencia actual de delta es coherente con la detención contractual ordenada por `/generate-bdd`. No constituye otro defecto alto independiente mientras F-01 impida legítimamente generarlo. Se conserva como limitación de esta revisión.

## Hallazgos nuevos

Ninguno en el material subsanado.

## Resolución para continuar

**El especificador debe decidir y documentar la reconciliación contractual de F-01 y concretar los límites observables de F-02.** Después podrá generarse el delta y someterse a revisión.

No se deriva ningún hallazgo al humano: el expediente no identifica un recurso externo imprescindible que los agentes no puedan conseguir. Tampoco procede trasladar el impedimento al desarrollador, porque su resolución determina el comportamiento exigible.

**Pregunta humana: ninguna.**
