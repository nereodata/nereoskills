# Evidencia roja de pruebas: T-ADV-0030

- **Prueba:** `skills.telegram_gateway.test_gateway_fondo.FondoTests.test_entradas_de_escucha_rechazan_token_ambiental_antes_de_efectos`
- **Base:** `869d9e9` (`release/v1.0`, antes de la implementación), en un worktree aislado y eliminado tras la ejecución.
- **Comando:** `python -m unittest skills.telegram_gateway.test_gateway_fondo.FondoTests.test_entradas_de_escucha_rechazan_token_ambiental_antes_de_efectos`
- **Datos:** tokens ficticios, destinatarios `111`/`222`; transporte, reserva de PID, escucha y `Popen` simulados.
- **Resultado:** `FAILED (failures=13)`, 1 prueba en 0.049 s. Los doce subcasos (CLI, `--fondo` y `--gestionado`; token local ausente o vacío/espacios; IDs ambientales o locales) fallan con `La escucha aceptó un token que solo autoriza avisos`. La aserción agregada confirma además que se llamó a `Popen` cuatro veces en el estado previo.
- **Conclusión:** el rojo se debe a que el estado previo permitía arrancar el gateway con el token ambiental; no depende de red, procesos reales, imports ni preparación del fixture.
