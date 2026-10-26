# Reproduccion roja B-ADV-0005

Ejecutado con `adevv orquestar --verificar "python -m unittest discover -s skills/orquestar -p test_arnes_ausente.py"` sobre produccion sin modificar de 1bf74f4 y las pruebas recuperadas/ampliadas.

Ran 8 tests in 0.055s; FAILED (failures=2, errors=9).

Las ausencias en agente y paso producen SystemExit: No se encuentra el arnes en el PATH; gateway produce RuntimeError sin recorrer reservas. El evento arnes no existe. La cadena de tres configuraciones falla en sus tres consumidores antes de alcanzar agy. La cuota anterior tampoco sobrevive al SystemExit de la ultima reserva. Imports, fixtures y sintaxis correctos: el caso operacional del paso se aisla sin progreso en disco para no activar la recuperacion existente de pasos completados pese a retorno no cero. Sin procesos externos ni Telegram real.
