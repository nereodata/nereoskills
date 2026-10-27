---
id: B-ADV-0017
title: "Tras recargar de versión, el gateway deja de escribir en telegram.log y acumula --root repetidos"
type: bug
weight: 25
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
origen: "Diagnóstico del chat de Telegram (2026-10-27): el gateway contesta «mira el log del gateway», pero telegram.log no se escribe desde el 2026-10-26 13:21"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0017: Tras recargar de versión, el gateway deja de escribir en telegram.log y acumula --root repetidos

## 🎯 Descripción del Fallo

**Comportamiento observado**:
- Los gateways de Adevv, Afinn y Adayy se recargaron a la 0.6.1 el 2026-10-27 a la 01:07 y siguen vivos. Sin embargo, `telegram.log` no recibe nada desde la recarga anterior: su última línea es «[gateway] recargado a versión 0.6.0», del 2026-10-26 a las 13:21. Los errores de `escuchar()` (`print(f'[gateway] error con el mensaje …')`) se pierden, y la respuesta al usuario («No he podido procesarlo; mira el log del gateway») remite a un log vacío.
- La línea de órdenes crece con cada recarga: `gateway.py --root <R> --gestionado --root <R> --root <R>`.

**Causa probable**: en `recargar_version()` (`skills/orquestar/orquestar.py`, hacia la línea 218), el sucesor se lanza con `subprocess.Popen([...], cwd=root, env=env, **opciones)`, sin `stdout` ni `stderr`. En Windows, los descriptores de Python no se heredan por defecto (PEP 446) y `CREATE_NO_WINDOW` no tiene consola, así que la salida del sucesor no llega a ninguna parte. Además, para `etiqueta == 'gateway'` se añade `--root` a `sys.argv[1:]`, que ya lo trae. Hay que comprobar si al bucle (`orquestar.log`) le pasa lo mismo cuando se recarga.

**Comportamiento esperado**:
1. El sucesor escribe en el mismo log que el proceso al que sustituye: `telegram.log` para el gateway y `orquestar.log` para el bucle, abierto en modo añadir y en UTF-8.
2. Cada recarga deja una línea en ese log con la versión nueva.
3. Los argumentos no se duplican: `--root` solo se añade si no está ya.
4. El mensaje de error al usuario incluye un motivo breve (por ejemplo, el perfil y la causa, como ya hace el mensaje de «ningún arnés disponible») para no depender del log.
5. Pruebas: tras una recarga simulada, el sucesor escribe en el log y su línea de órdenes no tiene argumentos repetidos.

## Triaje de alcance · reanudación 2026-10-27

- Causa comprobada: el sucesor carecía de redirección explícita y se añadía `--root` sin normalizar. El commit 92fb785 ya incorpora el arreglo y corrige las cadenas y el orden de confirmación señalados por Hades; se retoma ese trabajo sin reimplementarlo.
- Subfase A: [SKIP] Restauración del comportamiento esperado ya definido en este bug, sin requisito nuevo.
- Subfase B: [SKIP] Redirección estándar de subprocess al log existente y normalización local de argumentos; sin cambio de arquitectura.
- Subfase C1: [EXEC] Regresiones de escritura real stdout/stderr en UTF-8 y append, argumentos históricos duplicados y ausencia de confirmación si falla lanzamiento/publicación del PID; motivo breve en respuesta del gateway.
- Subfase C2: [EXEC] Completar únicamente los huecos que revelen esas regresiones del arreglo existente.
- Subfase D: [EXEC] Hades revisa pruebas y después el delta completo desde el padre de 92fb785, incluidos H1/H2 anteriores.
- Subfase E: [SKIP] No cambia el uso público; validación operativa en revisión de versión.
- Subfase F: [EXEC] Cierre y commit del bug en release/v1.0.
- Verificación al cierre: `python -m unittest skills.orquestar.test_recarga skills.telegram_gateway.test_firma_gateway skills.telegram_gateway.test_recarga_gateway tests.test_telegram_gateway tests.test_updater`, que cubre transferencia, gateway y actualización; además `git diff --check` y compilación de los módulos Python del delta, siempre con `adevv orquestar --verificar`. Sin suite completa ni herramientas de lint/tipado/secretos configuradas; sin cambios de dependencias.
- Decisión sin preguntar: conservar dificultad media promovida por el bucle, reanudar en release y mantener el protocolo de PID y los logs existentes.
