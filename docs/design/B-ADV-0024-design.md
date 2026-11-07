# B-ADV-0024 · Tratamiento unificado de cuotas supuestas y sondeo en Telegram Gateway

Reutilizar la clasificación de cuotas de `fallo_cuota` y la regla de sondeo de `configuraciones_con_cuota` del motor de orquestación en el módulo `skills/telegram_gateway/gateway.py`. Al alinear el gateway con B-ADV-0020, las cuotas sin hora de reinicio o por falta de créditos dejan de tratarse como un agotamiento rígido de 30 minutos (1800 s) y pasan a ser marcas supuestas de intervalo configurable (`cuota_reintento_s`, 300 s por defecto) con sondeo periódico y aviso de créditos una sola vez por episodio.

## Cambios técnicos

1. **`skills/telegram_gateway/gateway.py::invocar()`**:
   - Sustituir la asignación fija de `espera_cuota(salida)` por `motor.fallo_cuota(root, harness, modelo, salida)` cuando `codigo != 0` y la salida evidencia cuota.
   - Registrar la métrica con `tipo='gateway'`, incorporando los campos clasificados `cuota_tipo`, `cuota_origen`, `modelo_cuota` y `cuota_espera_s`.
   - Limitar sondeos y emitir aviso de créditos mediante `fallo_cuota`.
   - En respuestas exitosas (`codigo == 0`), invocar `motor.recuperar_cuota(root, harness, modelo)` para invalidar marcas previas y limpiar sondeos pendientes.

2. **`skills/telegram_gateway/gateway.py::conversar()`**:
   - Obtener candidatos elegibles mediante `motor.configuraciones_con_cuota(root, configs_originales)`.
   - Para las configuraciones omitidas por cuota no elegible para sondeo, preservar el diagnóstico detallado `f"{perfil}: cuota hasta {hasta}"` en `motivos` sin invocar el arnés.
   - Permitir que las configuraciones con cuota supuesta cuyo intervalo de sondeo haya vencido (o en sesión limpia) sean sondeadas en su orden de prioridad.

3. **`skills/telegram_gateway/SKILL.md`**:
   - Alinear la descripción de selección de modelos y cuotas: saltar modelos con cuota vigente confirmada o sospechas antes de vencer su intervalo de sondeo; permitir sondeos periódicos y al reiniciar.

## Mapa de impacto

- `invocar()`: emite métricas con esquema completo de cuota compatible con `orquestar_metricas.jsonl` y `/agentes`.
- `conversar()`: consume `configuraciones_con_cuota`, eliminando la divergencia entre el bucle de reservas del gateway y los de `bucle()` / `agente()`.
- Pruebas unitarias: actualizar `skills/telegram_gateway/test_reservas.py` para verificar `cuota_tipo: supuesta`, espera de 300 s en cuotas sin hora, sondeo tras intervalo y recuperación con respuesta exitosa.
