---
id: B-ADV-0020
title: "Una marca de agotado sin hora de reinicio impide usar un modelo que ya tiene cuota, incluso al relanzar"
type: bug
weight: 15
dificultad: media
version: "v1.0.0"
status: planned
depende_de: []
origen: "Reporte del usuario (2026-10-27): con cuota de Codex disponible, el bucle esperaba hasta las 09:07 o pasaba a Claude"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0020: Una marca de agotado sin hora de reinicio impide usar un modelo que ya tiene cuota, incluso al relanzar

## 🎯 Descripción del Fallo

**Causa raíz**:
- Cuando la salida de un arnés encaja con `CUOTA` pero no trae hora de recuperación, `espera_cuota()` (`skills/orquestar/orquestar.py`, hacia la línea 1506) supone 1800 s. Esa espera se guarda en `orquestar_metricas.jsonl` (`modelo_cuota`, `cuota_espera_s`).
- Antes de cada paso, `configuraciones_con_cuota()` (hacia la línea 1042) y `consumo_cuotas()` (hacia la línea 2030) descartan el perfil sin intentarlo mientras dure la marca.
- La marca sobrevive al relanzar el bucle y no hay forma de borrarla.

**Comportamiento observado** (2026-10-27):
- A las 08:37, Codex respondió `Your workspace is out of credits. Add credits to continue.` y quedó marcado «agotado hasta 09:07».
- Con los créditos ya repuestos, el bucle relanzado a las 08:53 descartó `codex/gpt-6.1-sol` sin probarlo y esperó hasta las 09:13. Después de añadir una reserva de Claude, pasó a Claude.
- En todos los casos usó un modelo peor o esperó sin necesidad.

**Comportamiento esperado**:
1. **Marca a ciegas, solo una sospecha**: se distingue una marca con hora real (el arnés dice cuándo reinicia, por ejemplo «Resets in 56h48m9s», que B-ADV-0016 debe reconocer bien) de una supuesta (sin hora). Mientras dure una marca supuesta, el perfil no se descarta del todo. Se hace un intento corto de comprobación, como mucho uno cada pocos minutos (por ejemplo, 5, configurable). Si responde, se borra la marca y se usa.
2. **Al relanzar se comprueba**: al arrancar `adevv orquestar`, las marcas supuestas no impiden probar el perfil en el primer paso. Las marcas con hora real se respetan.
3. **Sin créditos o problema de facturación**: errores como `out of credits`, `credit balance` o `billing_hard_limit` no se resuelven esperando, sino cuando la persona recarga. Se avisa por Telegram una sola vez, con un mensaje distinto del de cuota («sin créditos en codex: recarga y el bucle lo reintentará»), y se tratan como marca supuesta (punto 1), no como espera fija.
4. **Orden para borrar marcas**: `adevv orquestar --cuota-reset [harness[/modelo]]` borra las marcas vigentes de ese arnés o modelo, o todas si no se indica ninguno. Las borra registrando una entrada de recuperación en las métricas, sin reescribir el histórico. `--estado` y `--agentes` dejan de mostrarlo como agotado, y un bucle en espera de cuota lo nota en su siguiente comprobación y continúa sin relanzar.
5. **`--agentes` y `--estado`**: indican si cada marca es real o supuesta y su origen (por ejemplo, «agotado hasta 09:07, supuesto: sin hora en la respuesta»).
6. **Pruebas**:
   - Una marca supuesta se prueba al relanzar y se borra si el arnés responde.
   - Una marca real no se prueba antes de tiempo.
   - `--cuota-reset` hace que el perfil vuelva a elegirse.
   - Un bucle en espera continúa tras `--cuota-reset`.
   - «out of credits» genera el aviso de créditos.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario lo ha pedido expresamente. Incluye la orden nueva `--cuota-reset` y los cambios de requisitos y escenarios del bucle que hagan falta. Se puede tocar cualquier ruta necesaria.
