# Fase roja: T-ADV-0021

Antes de modificar producción, `adevv orquestar --verificar "python -m unittest skills/orquestar/test_cuota_vigente.py"` terminó con código 1: 8 tests, 8 fallos de aserción y 0 errores de preparación/sintaxis/importación (algunos tests tienen subcasos).

- `bucle()` ejecuta titular en vez de intermedia pese a agotamiento vigente.
- El modelo implícito agotado ejecuta predeterminado en vez de intermedia.
- Titular e intermedia agotados ejecutan titular en vez de última.
- Segunda revisión vuelve a titular pese al agotamiento persistido en la primera.
- Todas agotadas lanzan 3 veces en vez de conservar solo la última.
- Las tres variantes de rebote (`cuota_espera_s`, `sin_cuota`, `modelos: {}`) cuentan 5 llamadas en vez de 4.

Las regresiones de expiración y falta de reservas ya pasan y protegen compatibilidad. La prueba del modelo predeterminado se ajustó antes de esta ejecución para producir una aserción explícita en vez de un error al buscar un flag ausente.

Comprobación sintáctica de las pruebas: `adevv orquestar --verificar "python -m py_compile skills/orquestar/test_cuota_vigente.py"`, código 0. Sin herramientas de lint/tipado configuradas ni dependencias nuevas.
