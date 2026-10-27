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

## Bloqueo de especificación · 2026-10-27
Hades rechaza `/review-spec`: H1 (alta), H2/H3 (medias), todos `para: especificador`, `destino: resolver`. Aplicada regla 5 de `/orquestar`; avance conservado en `wip/B-ADV-0020` (7650397), release restaurada al estado previo salvo el enrutado y los informes.

El especificador debe concretar los casos históricos sin clasificación y duración distinta de 1800 segundos, el intervalo con opción ausente y la conservación de las restricciones de pares ajenos al reset. Detalle y reporte en `docs/review/versions/v1.0-revision.md` y `docs/review/spec_reviews/B-ADV-0020-spec-review.md`.

Triaje de este cierre por bloqueo: [EXEC] enrutado documental y `adevv orquestar --verificar "git diff --check"`; [SKIP] implementación y pruebas funcionales, pendientes de especificación aprobada. No se ha corregido el fallo ni ejecutado la suite completa.

## Triaje de alcance
- Subfase A: [EXEC] Requisito y escenarios de recuperación de cuotas supuestas, créditos y reset.
- Subfase B: [EXEC] Eventos compatibles en métricas y política común de selección/espera.
- Subfase C1: [EXEC] Regresiones aisladas de selección, reinicio, recuperación, CLI, espera y avisos.
- Subfase C2: [EXEC] Motor de orquestación, sin modificar la instalación.
- Subfase D: [EXEC] Hades sobre todo el delta.
- Subfase E: [EXEC] README y manual de orquestar.
- Subfase F: [EXEC] Cierre y commit en release/v1.0.
- Verificación al cierre: `python -m unittest discover -s skills/orquestar -p test_*cuota*.py` y módulos afectados `test_fallos_arnes`, `test_arnes_ausente`, `test_estado_agentes`, `test_informe_agentes`, más `tests.test_orquestar`; cubren persistencia, selección, avisos, CLI y reservas. `git diff --check` y compilación de los Python modificados. No suite completa.
- DEC: intervalo configurable `cuota_reintento_s` en orchestration.json, por defecto 300 segundos, positivo. El intento de comprobación usa el propio paso/revisión pendiente: evita trabajo artificial y permite aprovechar la respuesta.
- DEC: los registros históricos de 1800 segundos sin clasificación son supuestos (antiguo valor por defecto); los demás conservan la recuperación registrada por compatibilidad. Nuevos registros declaran explícitamente el origen.
- DEC: un nuevo proceso puede comprobar una sospecha aunque no hayan transcurrido los 300 segundos; dentro del proceso se respeta el intervalo. El reset y un éxito agregan recuperación al histórico; no alteran tokens ni datos previos.
- Cambio de contrato autorizado: las aserciones antiguas de espera fija 1800 s ante `quota` sin hora pasarán a 300 s. Los escenarios anteriores se conservan; el requisito humano de este bug sustituye la espera fija descrita en el manual de orquestar.

- Verificación de este intento interrumpido en especificación: solo `git diff --check`; no hay código ni pruebas nuevas, por lo que la verificación funcional del triaje queda pendiente del desarrollo.


## Especificar · 2026-10-27

- DEC-ESP-20-01: recuperar solo el bloque BDD y el triaje del WIP, sin fusionar diseño ni otros artefactos. Se descarta reanudar desarrollo dentro de este paso: Atenea concreta el contrato y Artemisa implementará después.
- DEC-ESP-20-02 (H1): el caso histórico de 3600 segundos, con 60 transcurridos, mantiene 3540 segundos de restricción al relanzar. Se descarta tratar todo registro sin clasificación como supuesto: solo el antiguo valor por defecto de 1800 segundos se interpreta así.
- DEC-ESP-20-03 (H2): la ausencia de cuota_reintento_s tiene un escenario propio y fija 300 segundos, igual que los valores inválidos. Se descarta equiparar cobertura de null a propiedad ausente.
- DEC-ESP-20-04 (H3): el reset recupera exclusivamente los pares seleccionados. Los ajenos parten de marcas confirmadas vigentes y conservan restricción y visualización hasta su recuperación. Se descarta el pronombre ambiguo «esos perfiles».
- Triaje de este paso: [EXEC] especificación, revisión aislada de Hades y `adevv orquestar --verificar "git diff --check"`; [SKIP] diseño, implementación y pruebas funcionales hasta el siguiente paso de desarrollo. La suite completa corresponde al bucle al cerrar versión.

- Cierre de especificación: Hades APROBADO, 9/10, ronda 3; H1, H2 y H3 resueltos, sin hallazgos nuevos. Desarrollo funcional pendiente. Véase docs/review/spec_reviews/B-ADV-0020-spec-review.md.
