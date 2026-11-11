**Veredicto:** APROBADO · **9,75/10**

# B-ADV-0044 · Reevaluación de las pruebas C1 de D9

La regresión reproduce el cierre indebido en los tres consumidores. El control positivo acredita que una aprobación histórica propia de B, también sin huella, permite avanzar. C1 queda aprobada para pasar a la corrección de D9 en C2.

## Reproducción y control

`test_confirmar_copia_historica_de_a_no_cierra_b_rechazado` parte de una ficha antigua en estado `completed`. Confirma A junto con un informe sin huella que acredita que `doble(3)` devuelve 6. En el siguiente commit cambia la función para que devuelva 3 y registra el rechazo de B. Después restaura desde el commit de A únicamente la ruta del informe y confirma la copia. El producto sigue siendo B. La prueba conserva el commit del rechazo como base para evaluar el cierre tras error.

| Consumidor | Comportamiento exigido tras confirmar la copia | Resultado observado |
|---|---|---|
| Selector | Elegir `revisar-tarea` para `B-DEMO-0001` | Eligió `revisar-version` para `v1.1.3`. |
| Preflight de versión | Incluir `B-DEMO-0001` entre los pendientes | El ID estaba ausente. |
| Cierre tras error de `bug-fix` | Devolver `False` con el rechazo de B como base | Devolvió `True`. |

Los tres subtests alcanzaron su aserción. El control `test_aprobacion_historica_de_b_tras_rechazar_b` pasó en la misma ejecución. Tras una aprobación escueta de A y el rechazo de B, un informe sin huella con la explicación propia «El doble es correcto.» llevó el selector a `revisar-version` y dejó vacío el preflight. Esto permite detectar también una corrección que bloquee toda aprobación histórica sin huella.

## Hallazgos anteriores y efecto del delta

- **Pruebas H1–H4 y N1–N9 · resueltos** en sus recorridos acreditados. El diff desde C1 añade un único método con repositorio Git temporal propio. Conserva la preparación compartida, los auxiliares y las aserciones anteriores. N9 se ejercitó como control positivo en este árbol.
- **Producto D3, D6, D7 y D8 · resueltos** en los recorridos acreditados por las revisiones anteriores. La ejecución actual confirma el recorrido de D6 con rechazo previo de B. La valoración de los demás recorridos se apoya en su evidencia histórica y en la lectura del delta.
- **Producto D9 · 🔴 crítico · persiste.** Para: `desarrollador` (Artemisa). Destino: `resolver` en C2. Conservar la procedencia del informe al confirmar la copia de A. El cierre exige que los tres consumidores mantengan pendiente B en ese historial y que el control positivo siga aceptando su aprobación propia.

**Hallazgos nuevos de pruebas:** ninguno.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 10/10 | Cubre la copia confirmada, los tres consumidores exigidos por D9 y el control de aprobación propia de B. |
| Aserciones | 9/10 | Fijan paso e ID, presencia del ID entre los pendientes y decisión de cierre respecto del commit de rechazo. El preflight se observa a través de su diagnóstico textual. |
| Rojo correcto | 10/10 | Los tres fallos son decisiones de cierre observadas después de preparar el historial. El control positivo pasa. |
| Estabilidad | 10/10 | Cada prueba crea su repositorio temporal, aísla la configuración de Git y obtiene las referencias de sus propios commits, sin depender del reloj ni del orden de ejecución. |

**Evidencia reutilizada.** Árbol `c71be17f14e80d87a904bbeb4e17ca7d469d2039`. El archivo local de pruebas coincide con el blob `f8726f2a06a874a6ed704cbe0724b076d7f146de` de ese árbol. La ejecución dirigida del 11 de noviembre de 2026 a las 22:22:01 registró dos pruebas en 4,120 s, tres subtests fallidos en D9 y un control positivo verde (código 1). Ruff selectivo (`E9,F63,F7,F82`) pasó sobre el mismo archivo a las 22:22:06 (código 0). El proyecto carece de comprobador de tipos configurado.
