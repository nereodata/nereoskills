# Revisión de código — B-ADV-0006

**Estado actual: SUPERADO.** H1–H4 resueltos en la reevaluación del árbol `671a1a0139d6e387092ae685a1e3d058ea7d2c4f`. Ver [aprobación de código — 9/10](B-ADV-0006-code-review.md). Se conserva a continuación el informe original como historia de la primera ronda; sus acciones ya están cerradas.

**Veredicto histórico de la primera ronda: RECHAZADO**

## Alcance y evidencia

Aplicadas las instrucciones de Hades y `/review-code` de la instalación 0.6.0, ignorando el modelo del frontmatter. Revisado el delta completo respecto a `HEAD` de `skills/orquestar/orquestar.py`, `skills/orquestar/SKILL.md` y el documento del bug; también las adiciones de `CHANGELOG.md` y `docs/review/versions/v1.0-revision.md`. Contrastado con el triaje, `docs/design/B-ADV-0006-design.md`, `docs/requirements/platform_plan.md` y los reportes APROBADOS de especificación y pruebas. Se han leído los colaboradores necesarios para valorar parser, selección, promoción y avisos; no se modifica producción ni pruebas.

Evidencia reutilizada de `orquestar_evidencias.jsonl`, árbol `2e12bf365d55c390b59a26a920b5e41fc190d011`:

- `python -m unittest discover -s tests -p test_orquestar.py > .git/B-ADV-0006-motor.log 2>&1`: código 0; el log confirma **65 pruebas, OK**.
- `python -m py_compile tests/test_orquestar.py skills/orquestar/orquestar.py`: código 0.
- `git diff --check`: código 0.

No se han repetido comprobaciones ni ejecutado experimentos, pruebas, suite completa o llamadas reales a Telegram. Los fallos siguientes se deducen de la lectura de rutas que los casos verdes no discriminan.

## Análisis estático y seguridad

- Compilación y comprobación del diff: verdes, reutilizadas.
- Linter, tipado y escáner de secretos: no configurados para el delta.
- Inspección manual del delta: sin credenciales, tokens ni claves incorporados. Los errores se incluyen como texto indentado; el comando sigue siendo el configurado por el operador, sin introducir ejecución del texto de la salida.
- Dependencias: sin cambios. Se mantiene el motor existente, stdlib y archivos locales; no se observa una nueva dependencia inversa ni cambio de stack.

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Corrección | 6/10 | La identidad del comando falla en el entorno sin PyYAML y los avisos pueden exceder el límite del transporte. |
| Seguridad | 9/10 | Sin secretos incorporados ni nueva interpolación de salida en comandos. |
| Conformidad | 7/10 | El flujo sigue el diseño, pero no garantiza identidad estable ni aviso final en todos los casos admitidos. Falta cobertura específica del nuevo cambio de rama. |
| Calidad | 8/10 | Helper localizado y reutilización de promoción y parada; necesita cerrar las incompatibilidades señaladas. |
| Eficiencia | 9/10 | Captura en archivo temporal y lectura final acotada; mantiene la caché verde por árbol y comando. |
| Documentación | 8/10 | Documenta recuperación, límites y reanudación; conserva una afirmación imprecisa sobre la frecuencia de la suite. |

**Media: 7,83/10.** Dos hallazgos altos impiden aprobar. No se genera `B-ADV-0006-code-review.md`.

## Hallazgos

### H1 — 🟠 ALTA: la identidad persistida del comando no sobrevive al parser sin PyYAML

- **Referencia:** `skills/orquestar/orquestar.py:1614` y `:1630`; interacción con `frontmatter` y `adevv/yaml_lite.py::_parse_scalar`.
- **Evidencia:** el alta serializa `suite_comando` mediante `json.dumps(cmd)`, pero la búsqueda compara el valor leído directamente con `cmd`. El parser ligero quita las comillas exteriores sin desescapar el contenido. Por ejemplo, el comando `python -c "print(1)"` se escribe como `"python -c \"print(1)\""` y se lee conservando las barras de escape interiores; un comando con una ruta Windows también conserva las barras duplicadas.
- **Impacto:** en la instalación sin PyYAML prevista por el plan de plataforma, la siguiente recaída no encuentra el bug del mismo comando. Crea otro ID, pierde la continuidad del contador y puede evitar indefinidamente la promoción y la parada máxima. Los casos de identidad verdes usan comandos sin caracteres que requieran escape y no detectan este fallo.
- **Para:** desarrollador.
- **Destino:** resolver.
- **Corrección requerida:** garantizar ida y vuelta exacta del comando con el lector realmente disponible, sin exigir PyYAML. Añadir regresión con parser ligero, comillas y barras invertidas que conserve el ID y acumule las recaídas. Si se cambia un parser compartido, declarar y validar ese impacto.

### H2 — 🟠 ALTA: una salida larga impide entregar el aviso final por Telegram

- **Referencia:** `skills/orquestar/orquestar.py:1592`, `:1620` y `:1648`, a través de `parar → avisar → enviar`.
- **Evidencia:** la captura admite 32768 bytes y el motivo de parada incluye toda esa salida. `avisar` añade nombre del proyecto y firma; `enviar` realiza un único `sendMessage` sin fragmentación ni reducción. El campo `text` de ese método admite como máximo 4096 caracteres según la [documentación oficial de Telegram](https://core.telegram.org/bots/api#sendmessage).
- **Impacto:** con, por ejemplo, 5000 caracteres ASCII de errores al agotar intentos, el envío excede el límite; el error se absorbe y solo queda un diagnóstico en consola. El bucle se detiene sin que llegue al humano el aviso con ID y última salida requerido. Afecta también a bloqueos y cancelaciones con salida larga. Las pruebas verdes simulan `avisar`, por lo que no verifican esta adaptación al transporte.
- **Para:** desarrollador.
- **Destino:** resolver.
- **Corrección requerida:** adaptar este aviso al límite real, contando prefijo y firma: fragmentar la salida o enviar un resumen acotado con el ID y la cola relevante, manteniendo la evidencia completa en disco. Verificar el mensaje final con un transporte simulado y una salida que supere el límite, sin llamadas reales.

### H3 — 🟡 MEDIA: el cambio nuevo a la rama de cierre queda sin cobertura específica

- **Referencia:** `skills/orquestar/orquestar.py:2191–2196`; triaje, subfase B y selección de rama.
- **Evidencia:** las pruebas nuevas parten ya de `release/v0.1`. No discriminan el camino añadido que hace checkout desde otra rama ni su guardia de cambios pendientes, incluyendo el caso de cierre expresado como `PARAR`.
- **Impacto:** las 65 pruebas verdes no protegen que la suite y el alta del bug se ejecuten en la release seleccionada cuando el bucle arranca en otra rama, requisito explícito del diseño y parte del delta de producción.
- **Para:** desarrollador.
- **Destino:** resolver.
- **Corrección requerida:** cubrir desde otra rama la selección de release antes de verificar/registrar, y comprobar que con cambios pendientes se para sin checkout ni alta. Incluir el estado `PARAR` cuya rama se reconstruye a partir de la versión. Limitar la verificación al comando del triaje.

### H4 — 🟡 MEDIA: frecuencia documentada de la suite incompatible con la recuperación

- **Referencia:** `skills/orquestar/SKILL.md:36`.
- **Evidencia:** el párrafo modificado sigue afirmando que se pasa la suite «una sola vez por versión», aunque la recuperación descrita en el mismo documento vuelve a ejecutarla después de cada arreglo al regresar al cierre.
- **Impacto:** el contrato operativo da dos descripciones distintas de cuándo y cuántas veces se verifica el cierre.
- **Para:** desarrollador.
- **Destino:** resolver.
- **Corrección requerida:** describir la ejecución al alcanzar el cierre y su repetición tras los arreglos, conservando la reutilización de un verde para el mismo árbol y comando.

No se requiere intervención humana. Corresponde corregir el delta y solicitar reevaluación.
