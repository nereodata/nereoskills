---
id: B-ADV-0010
title: "Suite roja al cerrar v1.0: patrón prohibido en telegram_gateway.feature y /status con PID simulado"
type: bug
weight: 10
dificultad: sencilla
version: "v1.0.0"
status: planned
depende_de: []
origen: "Cierre de v1.0 (2026-10-27 01:08): el bucle paró con «la versión no tiene más tareas elegibles pero la suite falla (python -m unittest discover -s tests)», 163 pruebas, 2 fallos"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0010: Suite roja al cerrar v1.0: patrón prohibido en telegram_gateway.feature y /status con PID simulado

## 🎯 Descripción del Fallo

Con todas las tareas de v1.0 cerradas, `python -m unittest discover -s tests` da 2 fallos. Se reproducen también sin `TELEGRAM_BOT_TOKEN` ni `TELEGRAM_ALLOWED_USER_IDS`, así que no dependen del entorno.

### 1. `test_instructions_cleanliness` (@CA-F02-04)
`skills/telegram_gateway/features/telegram_gateway.feature` contiene 8 veces `python skills/telegram_gateway/gateway.py --gestionado` en las tablas de ejemplos. `python *.py` es un patrón prohibido en los archivos de instrucciones (F-02, uso sin rutas). Probablemente entró con las especificaciones de T-ADV-0023, T-ADV-0024 o T-ADV-0030 (commits c8ca47d, ba046de, 869d9e9).

**Esperado**: los escenarios describen el arranque gestionado sin rutas ni `python <script>`, igual que el resto de instrucciones (por ejemplo, con la orden instalada `adevv telegram --gestionado`, o con un marcador abstracto si el comando exacto no importa en el escenario). La prueba de limpieza no se relaja.

```
AssertionError: Se detectaron 8 coincidencias de patrones prohibidos:
[python_script] skills/telegram_gateway/features/telegram_gateway.feature: 'python skills/telegram_gateway/gateway.py' en contexto: '... | VACIO | 111 |       | python skills/telegram_gateway/gateway.py --gestionado | AUSENTE |...'
… (8 en total)
```

### 2. `test_telegram_gateway.GatewayTests.test_status_summarizes_loop_version_and_backlog`
La prueba simula un bucle en marcha escribiendo `1` en el fichero PID del bucle y espera que `/status` diga «bucle en marcha». Ahora dice «bucle parado». Lo más probable es que T-ADV-0025 (efd498d, utilidades de PID unificadas) haga que `/status` compruebe si el proceso está vivo: el PID 1 no existe en Windows.

**Esperado**: decidir cuál es el comportamiento correcto y ajustar el código o la prueba en consecuencia. Si comprobar que el proceso está vivo es lo correcto, la prueba simula un proceso vivo (por ejemplo, el PID propio o un parche de la comprobación). Si no lo es, `/status` vuelve al criterio anterior. Hay que revisar si otras pruebas que escriben `motor.PID` dependen del mismo supuesto, como `test_with_loop_running_only_the_inbox_is_written`.

```
AssertionError: 'bucle en marcha' not found in '*tmp…* · bucle parado\n*Fase:* PARAR Falta la idea: …\n*v0.1.0:* 0/1 cerradas · en curso T-ADV-0002\n*Backlog sin versión:* 0\n*Por registrar:* 1 (entre pasos del bucle)\n\n— Adevv v1.0.0'
```

## 📋 Reproducir
1. `python -m unittest tests.test_instructions_cleanliness tests.test_telegram_gateway`
2. Resultado: 25 pruebas, 2 fallos (los anteriores).

## ✅ Criterio de cierre
La suite completa (`python -m unittest discover -s tests`) pasa en verde, con y sin las variables `TELEGRAM_*` en el entorno.
