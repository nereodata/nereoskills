# Revisión de Pruebas: T-ADV-0018

- **Tarea**: `docs/plan/tasks/T-ADV-0018-auto-recarga-bucle-y-gateway-al-actualizar-version.md`
- **Archivos revisados**: `skills/orquestar/test_recarga.py`, `skills/telegram_gateway/test_recarga_gateway.py`
- **Referencia**: `CA-M-1`..`CA-M-4`, triaje C1 de `T-ADV-0018` y `DEC-P10`. Sin `.feature`, conforme al triaje.
- **Ronda**: Reevaluación tras corrección y ampliación del delta de pruebas (18 tests).
- **Veredicto**: **APROBADO**
- **Puntuación media**: **9.25 / 10**. Sin hallazgos críticos, altos ni nuevos.

## Puntuaciones (1-10)

| Criterio | Nota | Justificación |
| :--- | :---: | :--- |
| Cobertura | 10 | Los 18 tests (11 en `test_recarga.py` y 7 en `test_recarga_gateway.py`) cubren detección y reversión (`CA-M-1`), descartes de puntero/ruta/checkout, transferencia de argumentos/raíz/estado/PID, fallos de `Popen` y de publicación atómica (`os.replace`), no borrado de marcas por el proceso saliente, reanudación en `main` sin revalidar/rerreservar, prioridad de parada, recarga cooperativa en `bucle()` y `escuchar()` (`CA-M-2`, `CA-M-3`) y transferencia real entre subprocesos Python locales. |
| Aserciones | 9 | Comprueban los mensajes `[orquestar] recargado a versión 0.6.0` y `[gateway] recargado a versión 0.6.0` con `flush=True`, todos los argumentos pasados a `recargar_version` en ambos motores, la preservación de `--root` absoluto, la cancelación (`terminate`/`wait`) del hijo si falla la publicación del PID y el primer poll con `desde=43`. |
| Rojo correcto | 9 | Rojo original acreditado en la primera ronda (10 tests con 1 fallo y 12 errores sobre contratos aún inexistentes) y evolución a 18 tests en verde tras la implementación, verificando comportamiento real sin cumplirse por construcción. |
| Estabilidad | 9 | Directorios temporales aislados, entorno parcheado con `addCleanup`, mocks deterministas y subproceso Python local con `timeout` y limpieza garantizada en `finally` sin red ni reloj real. |

## Reevaluación de hallazgos anteriores

| Hallazgo anterior | Estado | Evidencia en las pruebas actuales |
| :--- | :--- | :--- |
| 🟡 MEDIA — Falta aserción del aviso de recarga y de los argumentos de `recargar_version` / continuación de `desde` en `escuchar()` | **resuelto** | `test_recarga.py:63` verifica `[orquestar] recargado a versión 0.6.0`; `test_recarga_gateway.py:24-25,47-58,69-79` verifica `(gateway.__file__, root, gateway.PID)`, la etiqueta `'gateway'`, el aviso `[gateway] recargado a versión 0.6.0`, la restauración de `desde=43` en `main()` sin `reservar()` y su uso en el primer `actualizaciones('token-falso', 43)`. |

## Hallazgos nuevos

Ninguno.

## Evidencia y alcance

Revisión estática de `skills/orquestar/test_recarga.py` y `skills/telegram_gateway/test_recarga_gateway.py` frente al reporte anterior, el triaje de `T-ADV-0018` y `DEC-P10`. Se reutiliza la evidencia registrada de `adevv orquestar --verificar "python -m unittest skills/orquestar/test_recarga.py skills/telegram_gateway/test_recarga_gateway.py"` (18 tests en verde tras el rojo inicial registrado).
