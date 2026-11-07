# B-ADV-0024 · Evidencia de Fase Roja

Comando: `python -m unittest skills/telegram_gateway/test_reservas.py`

Fecha: 2026-11-07, antes de modificar código de producción en `skills/telegram_gateway/gateway.py`.
Resultado: 9 pruebas, 2 fallos de aserción reproduciendo exactamente los defectos reportados.

## Detalle de fallos observados

1. `test_cuota_sin_hora_clasificada_como_supuesta_sondeo_y_recuperacion`:
   - `AssertionError: None != 'supuesta'`
   - Causa: `invocar()` registra cuota directa con `espera_cuota(salida)` sin usar `fallo_cuota()`, por lo que no clasifica `cuota_tipo: 'supuesta'` ni fija `cuota_espera_s: 300` para cuotas sin hora en la respuesta. Además, utiliza la reserva `claude/m2` alineada con el escenario Gherkin.

2. `test_creditos_aviso_unico_por_episodio_en_gateway`:
   - `AssertionError: expected call not found.`
   - `Expected: avisar(..., 'cuota', 'Sin créditos en codex: recarga y el bucle lo reintentará')`
   - Causa: `invocar()` no invoca `fallo_cuota()`, omitiendo el aviso específico de agotamiento de créditos una vez por episodio. La prueba comprueba la repetición tras vencer los 300 s (`12:05:00`), verificando que se realiza el segundo lanzamiento y no se duplica el aviso de créditos.

Los fallos provienen de la lógica de cuota del gateway y no de errores de importación, red o arnés.
