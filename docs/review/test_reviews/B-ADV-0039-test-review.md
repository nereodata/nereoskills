**Veredicto:** RECHAZADO

Hades por `adevv orquestar --agente hades --prompt-file`, referencia de árbol comunicada 13e01c00ff. Informe transcrito de su salida porque falló la herramienta al guardar el archivo. Alcance: pruebas del delta, helpers, corrección de T1, regresión temporal de C2 y actualización histórica de ReservaCuotaTests. Sin revisión de producción ni ejecución de comprobaciones.

| Criterio | Puntuación |
|---|---:|
| Cobertura | 8/10 |
| Aserciones | 7/10 |
| Rojo correcto | 8/10 |
| Estabilidad | 9/10 |
| Media | 8/10 |

T1 resuelto en pruebas: el contraste combina revisión A pendiente, B aprobada, progreso parcial y árbol limpio; exige código 2, agy/gemini y bloqueo_agente sin cuota al principal. El helper persiste estado y revisión canónica y simula HEAD y limpieza por separado. Firma y selección de estado siguen simuladas; no constituye prueba integral de Git/backlog.

## T2 · ALTA

- para: desarrollador
- destino: resolver
- Archivo: skills/orquestar/test_fallos_arnes.py, test_resumen_no_renueva_recuperacion_original.
- La prueba exige ausencia de ('agy', 'primero') en marcas_cuota al vencer. Las marcas conservan el vencimiento histórico; consumo_cuotas filtra vigencia. Vencer no equivale a registrar recuperación explícita.
- Corregir la prueba para exigir vencimiento original sin desplazar, anterior o igual al instante actual, y ausencia del par entre cuotas vigentes de consumo_cuotas. Mantener selección del primer proveedor, espera cero y vigencia del segundo.

La regresión histórica distingue tres intentos de un resumen sin consumo y verifica su proveedor/modelo. El RED comunicado demuestra continuidad indebida con commit parcial y selección temporal incorrecta. Disco temporal, reloj y proveedores controlados. Diff-check acreditado; lint/tipado no disponibles. Sin suite completa.

## Parada ordenada por el motor

Tras este dictamen: «Hades ha rechazado B-ADV-0039 2 veces seguidas: no sigas corrigiendo. Commitea lo que tengas en la rama [...] termina el paso sin cambiar estados». T2 queda pendiente; no se aplicaron más correcciones.
