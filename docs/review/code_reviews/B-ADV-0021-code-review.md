# Code Review: B-ADV-0021 — Volver atrás con bucles a un motor sin recarga lo mata

- **Veredicto**: APROBADO
- **Ronda**: 2 (reevaluación del delta sin commitear en `release/v1.0`)

## Análisis estático
- `git diff --check` solo marca una línea en blanco al final de `tests/test_updater.py` (hallazgo 5) y el aviso LF→CRLF de `skills/orquestar/test_recarga.py`. No hay manifiestos ni secretos en el delta.
- Batería del triaje (updater, recarga, gateway, cli, sync: 115 pruebas) en verde con `adevv orquestar --verificar` sobre este árbol; reutilizada, no relanzada.

## Criterios de aceptación
| CA | Resultado |
|---|---|
| CA-F03-17 (vuelta a 0.4.0 con bucle y gateway de 1.0.0) | ✓ los motores no ceden el PID y avisan una vez por versión activa con el texto de RF-F03-14. El aviso de instalación mantiene la frase literal y nombra los procesos en « En marcha: {lista}.» |
| CA-F03-18 (0.6.1 sin `--calidad`; gateway recarga; recarga posterior a 1.0.1) | ✓ comprobación por proceso con sus argumentos reales; frase literal del aviso intacta |
| H-07 (limpieza diferida y reintentada) | ✓ se reintenta fuera de pasos y sin bucles, y ya no busca procesos si no hay versiones antiguas |

## Hallazgos de la ronda anterior
- 🟠 1 El aviso de instalación pegaba la lista de procesos tras «reinicio manual» / «se detendrán»: **resuelto**. `mensaje_actualizacion` deja las frases de @CA-F03-17/18 tal cual y añade aparte « En marcha: {lista}.». Las pruebas comprueban ahora la frase completa, terminada en punto, seguida de « En marcha: ».
- 🟡 2 La limpieza añadía dos búsquedas de procesos a cada orden `adevv`: **resuelto**. `limpiar_versiones_antiguas` sale antes de `sincronizacion_bloqueada()` y `detectar_procesos_adevv()` si en `versions/` no hay ninguna carpeta aparte de la activa y las `.staging-*`. La guarda de bucles sigue por delante de cualquier borrado. Lo cubre `test_limpieza_sin_versiones_antiguas_no_detecta_procesos`.
- 🔵 3 Opciones abreviadas en `causa_sin_recarga`: **persiste**, con destino `descartar` como en la ronda anterior.
- 🔵 4 Clase de prueba tras `if __name__ == "__main__"`: **resuelto**. `TestAvisoRecargaYLimpieza` está ya antes del bloque `__main__`.

Delta de esta ronda: el ajuste de `test_bucle_transfiere_antes_de_calcular_paso` solo añade `intentos_dependencias` al estado que se transfiere, la misma clave que envía `bucle()`. No toca código de producción.

## Puntuaciones
| Criterio | Nota |
|---|---|
| Corrección | 9 |
| Seguridad | 10 |
| Conformidad | 9 |
| Calidad | 8 |
| Eficiencia | 9 |
| Documentación | 9 |
| **Media** | **9,0** |

## Hallazgos nuevos
- 🔵 **5. Línea en blanco al final de `tests/test_updater.py`**: destino `resolver`. `git diff --check` la marca («new blank line at EOF»). Basta con quitarla.
