**Veredicto:** APROBADO

Tercera revisión de B-ADV-0017 mediante `/review-code`, como Hades, el 2026-10-27. Alcance: delta completo desde `92fb785~1` hasta el árbol de trabajo (incluidos cambios sin commitear) en `skills/orquestar/orquestar.py` (`recargar_version`), `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/*`. No se modifica código de producción ni pruebas.

## Análisis estático

- Árbol revisado: `57429a7f8d`. Evidencia en verde registrada para ese árbol con `adevv orquestar --verificar "python -m unittest skills.orquestar.test_recarga skills.telegram_gateway.test_firma_gateway skills.telegram_gateway.test_recarga_gateway tests.test_telegram_gateway tests.test_updater"`, más `compileall` de los módulos del delta y `git diff --check`, todo en limpio. No se ha relanzado nada.
- Sin lint ni tipado configurados; sin cambios de dependencias (auditoría N/A); no aparecen secretos en el delta.

## Puntuaciones

| Criterio | Puntuación |
|---|---:|
| Corrección | 9 |
| Seguridad | 9 |
| Conformidad | 9 |
| Calidad | 9 |
| Eficiencia | 10 |
| Documentación | 9 |
| **Media** | **9,17** |

## Cumplimiento del comportamiento esperado

1. **Log del sucesor**: el sucesor se lanza con `stdout` apuntando a `root/telegram.log` (gateway) o a `root/orquestar.log` (bucle), con `stderr=STDOUT`, `stdin=DEVNULL`, el archivo abierto en modo `'a'` con UTF-8 y `PYTHONIOENCODING=utf-8`. Son las mismas rutas que usan los lanzamientos iniciales (`gateway.py:384`, `orquestar.py:2325`). ✅
2. **Línea de recarga**: se escribe `[<etiqueta>] recargado a versión <v>` en ese mismo log. ✅
3. **Sin argumentos repetidos**: para el gateway se eliminan todas las apariciones de `--root X` y `--root=X` antes de añadir una sola, así que se limpian también las líneas de órdenes ya contaminadas. El bucle no recibe `--root`. ✅
4. **Motivo breve al usuario**: `TipoExcepción: mensaje`, sin saltos de línea y limitado a 120 caracteres. Si el motivo rompe el Markdown, `enviar` reintenta en texto plano, así que el mensaje se entrega igual. ✅
5. **Pruebas**: la transferencia real comprueba que stdout y stderr del sucesor llegan en UTF-8 y en modo añadir, y que la confirmación aparece una sola vez. Hay pruebas de `--root` único, de `--root`/`--root=` históricos y de que no hay confirmación cuando fallan el lanzamiento o la publicación del PID. ✅

## Reevaluación de hallazgos anteriores

### H1 · 🟠 ALTA · Resuelto
La confirmación (`orquestar.py:234`) se escribe después de `os.replace(temporal, pid)` y ya no se imprime antes de `Popen`. Si `Popen` falla o falla la publicación del PID, el log no recibe la confirmación, y `test_fallo_lanzamiento_conserva_pid` y la prueba de fallo de publicación lo comprueban. La salida queda solo en el archivo (`print` eliminado), sin duplicados.

### H2 · 🔴 CRÍTICO · Resuelto
Las tres cadenas usan ahora la secuencia `\n` en una sola línea. `compileall` y la suite del triaje están en verde sobre el árbol revisado.

## Hallazgos nuevos

### N1 · 🟡 MEDIA · Fallo al escribir la confirmación tras publicar el PID — `resolver`
- **Ubicación**: `skills/orquestar/orquestar.py:234-235`.
- **Caso**: `log.write`/`log.flush` siguen dentro del `try` que captura `OSError`. Si fallan (disco lleno, por ejemplo) después de `os.replace`, se termina al hijo, pero el archivo PID ya contiene su PID y el proceso anterior sigue vivo sin ser propietario. Es improbable porque el archivo ya está abierto para añadir.
- **Corrección**: tratar la escritura de la confirmación como algo que no puede fallar, aislándola en su propio `try`/`except OSError: pass` o sacándola del bloque que deshace la transferencia, para que una vez publicado el PID no se deshaga.

### N2 · 🔵 BAJA · Detalle de la excepción visible en el chat — `descartar`
El motivo puede incluir rutas locales u otros datos internos de la excepción. Solo lo reciben usuarios autorizados y está acotado a 120 caracteres, así que el riesgo es hipotético.
