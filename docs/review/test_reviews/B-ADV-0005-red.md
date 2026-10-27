# Reproduccion roja B-ADV-0005

Pruebas finales con historiales aislados por consumidor y comparacion del instante con zona horaria, contra produccion original c9dbdc7. Ejecutadas mediante adevv orquestar --verificar; produccion restaurada despues. Fallo esperado: ejecutables ausentes abortan y el evento arnes no existe.

```text
EEEEE.FEEEEF

======================================================================

ERROR: test_agente_salta_ausente_con_sesion_nueva (test_arnes_ausente.ArnesAusenteTests.test_agente_salta_ausente_con_sesion_nueva)

Hades usa la reserva y no reanuda una sesi�n al cambiar de arn�s.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 88, in test_agente_salta_ausente_con_sesion_nueva

    self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)

                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1278, in agente

    sys.exit(f'No se encuentra el arn�s "{base[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "claude" en el PATH.



======================================================================

ERROR: test_cadena_intermedia_ausente_en_tres_flujos (test_arnes_ausente.ArnesAusenteTests.test_cadena_intermedia_ausente_en_tres_flujos) (flujo='agente')

Dos ausencias dejan dos evidencias y alcanzan la segunda reserva.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 151, in test_cadena_intermedia_ausente_en_tres_flujos

    self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 0)

                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1278, in agente

    sys.exit(f'No se encuentra el arn�s "{base[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "codex" en el PATH.



======================================================================

ERROR: test_cadena_intermedia_ausente_en_tres_flujos (test_arnes_ausente.ArnesAusenteTests.test_cadena_intermedia_ausente_en_tres_flujos) (flujo='paso')

Dos ausencias dejan dos evidencias y alcanzan la segunda reserva.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 153, in test_cadena_intermedia_ausente_en_tres_flujos

    codigo, esperar = self.bucle()

                      ^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 62, in bucle

    codigo = motor.bucle(args, self.root)

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 2116, in bucle

    codigo, m, salida = ejecutar(a, root, prompt, env=env, rol=cfg_actual, sesion=sesion_paso)

                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1223, in ejecutar

    cmd = comando(a, prompt, root, rol, sesion=sesion)

          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1055, in comando

    sys.exit(f'No se encuentra el arn�s "{plantilla[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "codex" en el PATH.



======================================================================

ERROR: test_cadena_intermedia_ausente_en_tres_flujos (test_arnes_ausente.ArnesAusenteTests.test_cadena_intermedia_ausente_en_tres_flujos) (flujo='gateway')

Dos ausencias dejan dos evidencias y alcanzan la segunda reserva.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 157, in test_cadena_intermedia_ausente_en_tres_flujos

    self.assertIn('agy/reserva-c', gateway.conversar(self.root, '123', 'hola'))

                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\telegram_gateway\gateway.py", line 200, in conversar

    codigo, s_id, resp = invocar(root, prompt, cfg, sesion=None)

                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\telegram_gateway\gateway.py", line 163, in invocar

    raise RuntimeError(f'No se encuentra el arn�s "{base[0]}" en el PATH.')

RuntimeError: No se encuentra el arn�s "codex" en el PATH.



======================================================================

ERROR: test_cuota_se_conserva_si_ultima_reserva_ausente (test_arnes_ausente.ArnesAusenteTests.test_cuota_se_conserva_si_ultima_reserva_ausente)

La recuperaci�n del principal sigue exactamente a las 18:00 UTC.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 184, in test_cuota_se_conserva_si_ultima_reserva_ausente

    self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)

                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1278, in agente

    sys.exit(f'No se encuentra el arn�s "{base[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "codex" en el PATH.



======================================================================

ERROR: test_gateway_salta_ausente_y_guarda_sesion_reserva (test_arnes_ausente.ArnesAusenteTests.test_gateway_salta_ausente_y_guarda_sesion_reserva)

La firma y persistencia pertenecen al arn�s que s� respondi�.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 108, in test_gateway_salta_ausente_y_guarda_sesion_reserva

    respuesta = gateway.conversar(self.root, '123', 'hola')

                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\telegram_gateway\gateway.py", line 193, in conversar

    codigo, s_id, resp = invocar(root, prompt, cfg, sesion=sesion)

                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\telegram_gateway\gateway.py", line 163, in invocar

    raise RuntimeError(f'No se encuentra el arn�s "{base[0]}" en el PATH.')

RuntimeError: No se encuentra el arn�s "claude" en el PATH.



======================================================================

ERROR: test_paso_salta_ausente_sin_espera (test_arnes_ausente.ArnesAusenteTests.test_paso_salta_ausente_sin_espera)

El paso contin�a inmediatamente con la reserva de otro arn�s.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 97, in test_paso_salta_ausente_sin_espera

    codigo, esperar = self.bucle()

                      ^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 62, in bucle

    codigo = motor.bucle(args, self.root)

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 2116, in bucle

    codigo, m, salida = ejecutar(a, root, prompt, env=env, rol=cfg_actual, sesion=sesion_paso)

                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1223, in ejecutar

    cmd = comando(a, prompt, root, rol, sesion=sesion)

          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1055, in comando

    sys.exit(f'No se encuentra el arn�s "{plantilla[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "claude" en el PATH.



======================================================================

ERROR: test_todos_ausentes_fallo_claro_sin_cuota (test_arnes_ausente.ArnesAusenteTests.test_todos_ausentes_fallo_claro_sin_cuota) (flujo='agente')

Ning�n flujo aborta silenciosamente ni espera cuota inexistente.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 123, in test_todos_ausentes_fallo_claro_sin_cuota

    self.assertNotEqual(motor.agente(self.root, 'hades', 'revisa'), 0)

                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1278, in agente

    sys.exit(f'No se encuentra el arn�s "{base[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "claude" en el PATH.



======================================================================

ERROR: test_todos_ausentes_fallo_claro_sin_cuota (test_arnes_ausente.ArnesAusenteTests.test_todos_ausentes_fallo_claro_sin_cuota) (flujo='paso')

Ning�n flujo aborta silenciosamente ni espera cuota inexistente.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 125, in test_todos_ausentes_fallo_claro_sin_cuota

    codigo, esperar = self.bucle(progreso=False)

                      ^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 62, in bucle

    codigo = motor.bucle(args, self.root)

             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 2116, in bucle

    codigo, m, salida = ejecutar(a, root, prompt, env=env, rol=cfg_actual, sesion=sesion_paso)

                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1223, in ejecutar

    cmd = comando(a, prompt, root, rol, sesion=sesion)

          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 1055, in comando

    sys.exit(f'No se encuentra el arn�s "{plantilla[0]}" en el PATH.')

SystemExit: No se encuentra el arn�s "claude" en el PATH.



======================================================================

FAIL: test_evento_filtrable_y_activo_por_defecto (test_arnes_ausente.ArnesAusenteTests.test_evento_filtrable_y_activo_por_defecto)

El nuevo evento usa el mismo filtro que los avisos existentes.

----------------------------------------------------------------------

Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 231, in test_evento_filtrable_y_activo_por_defecto

    self.assertIn('arnes', motor.EVENTOS)

AssertionError: 'arnes' not found in ('version', 'cuota', 'respuesta', 'error')



======================================================================

FAIL: test_todos_ausentes_fallo_claro_sin_cuota (test_arnes_ausente.ArnesAusenteTests.test_todos_ausentes_fallo_claro_sin_cuota) (flujo='gateway')

Ning�n flujo aborta silenciosamente ni espera cuota inexistente.

----------------------------------------------------------------------

RuntimeError: No se encuentra el arn�s "claude" en el PATH.



During handling of the above exception, another exception occurred:



Traceback (most recent call last):

  File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\test_arnes_ausente.py", line 129, in test_todos_ausentes_fallo_claro_sin_cuota

    with self.assertRaisesRegex(RuntimeError, 'ning.n arn.s disponible'):

         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

AssertionError: "ning.n arn.s disponible" does not match "No se encuentra el arn�s "claude" en el PATH."



----------------------------------------------------------------------

Ran 8 tests in 0.060s



FAILED (failures=2, errors=9)


```

## Regresión HC-01 (revisión de código)

`adevv orquestar --verificar "python -m unittest discover -s skills/orquestar -p test_arnes_ausente.py"`: nueve pruebas, dos fallos. El agente no registra ninguna señal sin_cuota (0 frente a 1); el paso no llama esperar(root, 2700). Cuota previa hasta 18:00Z y reloj 17:15Z, principal disponible y reserva ausente. Resto de pruebas en verde. Evidencia roja antes de corregir HC-01, sin suite completa.
