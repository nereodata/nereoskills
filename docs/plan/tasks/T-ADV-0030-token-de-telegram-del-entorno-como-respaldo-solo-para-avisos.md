---
id: T-ADV-0030
title: "El token de Telegram del entorno sirve de respaldo solo para avisos, sin arrancar gateway"
type: funcional
weight: 80
dificultad: sencilla
version: "v1.0.0"
status: planned
depende_de: ["B-ADV-0007"]
origen: "Petición del usuario: poner el token del bot de Adevv en las variables de sistema para que los proyectos que olviden su .env le avisen allí"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0030: El token de Telegram del entorno sirve de respaldo solo para avisos, sin arrancar gateway

## 🎯 Objetivo de Negocio
El usuario quiere definir el token del bot de Adevv (y sus usuarios) en las variables de sistema como respaldo: un proyecto que olvide su `.env` debe seguir avisando, a ese bot. Hoy `credenciales()` (`skills/orquestar/orquestar.py:1482`) toma el `.env` del proyecto y, si falta, el entorno, y trata igual ambos orígenes: con el token de respaldo, cada proyecto sin `.env` arrancaría además su gateway (`iniciar_gateway()`, `:1935`) escuchando el bot de Adevv. Telegram solo admite un lector por bot, así que chocaría (409) con el gateway real de Adevv y uno de los dos dejaría de escuchar.

Los avisos ya llevan el nombre del proyecto delante (`avisar()`, `:1531`), así que en el bot compartido se distingue el origen.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Origen de las credenciales):** `credenciales()` informa de si el token viene del `.env` del proyecto o del entorno de ejecución, sin cambiar la precedencia actual (`.env` primero).
- [ ] **CA-M-2 (Avisos con el respaldo):** con credenciales del entorno, `avisar()` sigue enviando los avisos del proyecto con su nombre delante, como hoy.
- [ ] **CA-M-3 (Sin gateway con el respaldo):** con credenciales del entorno, `iniciar_gateway()` no arranca el gateway del proyecto y lo dice una vez en la salida del bucle (p. ej. «[orquestar] token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto»). `adevv telegram` / `--fondo` lanzado a mano en un proyecto así se niega con el mismo motivo, salvo que el `.env` del proyecto defina el token (incluido el propio repositorio del bot, que lo tendrá en su `.env`).
- [ ] **CA-M-4 (Pruebas y documentación):** pruebas de los dos orígenes (solo `.env`, solo entorno, ambos) para avisos, autoarranque y arranque manual, sin red y sin heredar las variables `TELEGRAM_*` reales (B-ADV-0007); documentación en `skills/telegram_gateway/SKILL.md` y `skills/orquestar/SKILL.md` (credenciales y su respaldo).

## Especificación corregida · Atenea · 2026-10-26

Se resuelven H-01..H-05 del reporte conservado en `wip/T-ADV-0030:docs/review/spec_reviews/T-ADV-0030-spec-review.md`. No se fusiona ese WIP ni se recuperan código, tests o diseño. El historial confirma que la precedencia individual y el prefijo del aviso ya existen; son regresiones del cambio de origen/autorización, no funcionalidad nueva.

- **DEC-ESP-01 (H-01)**: token e IDs se resuelven independientemente, con `.env` primero y respaldo por campo ausente o vacío. Origen efectivo del token: `proyecto`, `entorno` o `ninguno`. Token local con IDs ambientales permite escuchar; token ambiental con IDs locales solo permite avisar. Sin token o sin IDs utilizables no hay avisos ni escucha; se conserva el diagnóstico de credenciales incompletas. Se descarta resolver la pareja como bloque porque cambiaría la precedencia actual. La forma de propagar el origen se decide en diseño.
- **DEC-ESP-02 (H-02/H-05)**: todos los ejemplos nuevos usan exclusivamente tokens `token-local-ficticio`/`token-entorno-ficticio`, usuarios 111/222 y proyecto `ProyectoDemo`. Se excluyen las variables `TELEGRAM_*` heredadas y se restaura el entorno al terminar, también ante fallos. Transporte, escucha y creación de procesos se sustituyen por observadores sin red ni procesos reales. Aviso de evento `version` y texto `Versión terminada`, con telegram habilitado: cada envío empieza exactamente por `[ProyectoDemo] Versión terminada`, conservando la firma existente. Se descartan credenciales reales y comprobaciones vagas del nombre.
- **DEC-ESP-03 (H-03)**: la política se aplica a `adevv telegram`, `adevv telegram --fondo` y la entrada interna `gateway.py --gestionado`. La entrada gestionada no es una nueva opción pública de la CLI. Rechazo ambiental con salida no cero, antes de reservar PID o crear un proceso o escuchar. Motivo común exacto: `token de Telegram del entorno: solo avisos; añade un .env para conversar con este proyecto` (se permite prefijo `[orquestar]`). Se descarta cubrir solo un modo.
- **DEC-ESP-04 (H-04)**: tres solicitudes de autoarranque en una ejecución del mismo bucle con respaldo y credenciales completas producen cero procesos/gateways y exactamente una nota con ese motivo. Un bucle nuevo vuelve a informar una vez; no hay persistencia entre ejecuciones. Con token local y condiciones disponibles se conserva el autoarranque positivo. Se descarta silenciar todos los autoarranques o repetir la nota por intento.

### Triaje de verificación

- **Especificar**: `/review-spec` aislado sobre los escenarios nuevos y los CA/DEC de esta tarea; `adevv orquestar --verificar "git diff --check"` para el delta documental. No hay implementación nueva que acreditar ni pruebas nuevas ejecutables en este paso.
- **Desarrollo posterior (C1/QA)**: mantener el comando del triaje original `adevv orquestar --verificar "python -m unittest tests.test_orquestar tests.test_telegram_gateway skills.telegram_gateway.test_gateway_fondo"`, con credenciales ambientales eliminadas, datos ficticios y sin red; compilación de ambos módulos y `git diff --check`. Automatizar los ejemplos nuevos y demostrar rojo por origen ausente/escucha ambiental permitida contra el estado previo; las aserciones de precedencia/prefijo son conservación del contrato. No escribir tests en especificar. La suite completa corresponde al bucle al cerrar versión.
- **Documentación posterior**: actualizar `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md` cuando se implemente la política, sin presentar ahora el comportamiento pendiente como disponible.
