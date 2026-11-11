**Veredicto:** APROBADO · **9,50/10**

# B-ADV-0044 · Reevaluación C1 de D10 y D11

Las tres pruebas añadidas reproducen cinco decisiones incorrectas. En D10 se identifica el commit exacto que libera B. En D11 se distingue cuándo Hades debe llamar a la reserva y cuándo debe terminar con el rechazo del principal.

## D10 · Procedencia de la aprobación

La prueba crea una ficha `completed` y cuatro commits en un repositorio temporal. A calcula correctamente el doble y recibe una aprobación de una sola línea, sin huella. El siguiente commit introduce el defecto en B y registra su rechazo. El tercero restaura desde A únicamente el informe. El cuarto añade a esa copia la fecha de archivo. El producto B y la referencia al commit de rechazo son los mismos en ambas observaciones.

| Consumidor | Tras confirmar la copia | Tras confirmar la nota |
|---|---|---|
| Selector | Pide `revisar-tarea` para `B-DEMO-0001`, como se exige. | Avanza indebidamente a `revisar-version`. |
| Preflight | Incluye el ID entre los pendientes. | Omite el ID. |
| Cierre tras error de `bug-fix` | Devuelve `False` con el rechazo de B como base. | Devuelve `True` con la misma base. |

El control `test_aprobacion_historica_de_b_tras_rechazar_b` pasó. Cuando la primera emisión propia de B tras el rechazo ya contiene su comprobación, el selector avanza a versión y el preflight queda vacío. El control preserva la compatibilidad con aprobaciones históricas sin huella.

## D11 · Dictamen propio y reserva autorizada

- **Solo hay un ejemplo HTML.** El principal termina con código cero y la aprobación aparece dentro de `<pre><code>`. La primera aserción que falla encuentra únicamente a Claude en las métricas. La prueba exige que el principal quede sin veredicto, que la reserva Codex registre su rechazo en la misma invocación y que se hayan llamado los dos perfiles configurados en orden.
- **Hay un rechazo propio después del ejemplo.** Las métricas atribuyen al principal la aprobación del ejemplo. La prueba exige el rechazo escrito después de `</code></pre>` y una sola llamada al perfil principal. Este caso detecta también una corrección que ignore el resto de la respuesta después del bloque HTML.

## Hallazgos y destino

- **Anteriores de C1 · H1–H4 y N1–N9, resueltos.** La ampliación conserva los auxiliares y todas las aserciones anteriores. **D9 de producto, resuelto** en los tres consumidores según la revisión D anterior. La ejecución de esta ronda vuelve a acreditar el control positivo de B.
- **Nuevo de pruebas · N10 · 🟡 Media.** Los dos casos HTML entran por la respuesta del proveedor. El informe canónico es la otra entrada identificada en D11. Una corrección limitada a la respuesta del arnés podría satisfacer ambos tests y dejar que el preflight acepte un ejemplo archivado. **Responsable** `desarrollador` (Artemisa). **Destino** `resolver` en C2. En una ficha `completed`, guardar el ejemplo como único posible dictamen en el informe canónico y comprobar que el preflight mantiene pendiente el ID.
- **De producto · D10 🔴 crítico y D11 🟠 alto, persisten.** **Responsable** `desarrollador` (Artemisa). **Destino** `resolver` en C2. D10 debe conservar las tres decisiones observadas tras la copia también después de la nota. D11 debe respetar el límite del ejemplo HTML y el rechazo propio que lo sigue.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Cobertura | 9/10 | D10 cubre las dos etapas y los tres consumidores. D11 cubre los dos resultados del proveedor. N10 identifica el límite en la lectura desde disco. |
| Aserciones | 9/10 | Verifican paso e ID, decisión de cierre, veredicto por proveedor, identidad de invocación y llamadas efectivas. El preflight se observa por la presencia del ID en su diagnóstico textual. |
| Rojo correcto | 10/10 | Los cinco fallos son de aserción en las decisiones previstas. Pasan la etapa previa a la nota y el control positivo. |
| Estabilidad | 10/10 | Git opera en un repositorio temporal con configuración aislada. Las referencias proceden de sus commits, la nota tiene fecha fija y los proveedores son simulados. |

**Alcance y evidencia.** Frente al C1 de `c71be17f14`, el delta añade solo tres métodos a `skills/orquestar/test_progreso.py`. El triaje conserva sus regresiones de parada tras dos intentos, avance parcial en fichas antiguas y WIP, pasos de análisis, alternancia por ID, recarga y reinicio manual, perfiles, consumo, cuota y cierre revisado tras error. La evidencia histórica de la ronda D recoge 166 pruebas dirigidas verdes antes de esta ampliación. B-ADV-0045, 0046 y 0047 tienen revisión propia.

El archivo local de pruebas coincide con el del árbol `51f8328d7e41b1b45975db7554557807dd3fe4af`. La evidencia adjunta del 11 de noviembre de 2026 registra cuatro pruebas en 6,741 s, cinco fallos de aserción y un control positivo verde. Ruff selectivo (`E9,F63,F7,F82`) terminó con código 0. El proyecto carece de comprobador de tipos configurado. El dictamen se basa en las pruebas, los escenarios y la evidencia aportada.
