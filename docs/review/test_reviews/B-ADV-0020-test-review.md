# Revisión de pruebas B-ADV-0020

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Modo: orquestado. Ronda 4.

## Alcance y aislamiento

Base estable: 3f53a3c7ecd707733e58cecf5041bf3d25def4b9. Revisión del delta COMPLETO de pruebas: nuevo skills/orquestar/test_cuota_supuesta.py y modificaciones de test_cuota_vigente.py, test_fallos_arnes.py, test_arnes_ausente.py y test_estado_agentes.py en ese directorio, más tests/test_orquestar.py. Se leen los fixtures, estímulos, mocks y aserciones afectados; se contrastan con todo el bloque @B-ADV-0020 aprobado y el contrato del bug. Los escenarios anteriores permanecen.

Se leyeron Hades, review-test y review-code instalados en C:/Users/Iván Moreno/.adevv/versions/0.6.1, ignorando el modelo. Esta fase se realizó aislada de producción y diseño, antes de review-code. Se reutiliza el informe anterior para reevaluar T1–T3 y se examinan las nuevas regresiones de C1–C3.

## Evaluación del delta completo

| Artefacto | Evaluación |
| --- | --- |
| test_cuota_supuesta | Cubre los once escenarios/esquemas: recuperación al relanzar, marcas reales, históricos 1800/3600, intervalos y propiedad ausente, reset selectivo/global, despertar, créditos y visualización. Mantiene la prueba sin reserva con cero lanzamientos a los 299 segundos y titular a los 300. Añade tres regresiones deterministas de C1–C3. |
| test_cuota_vigente | Conserva los escenarios de perfil único y todas las reservas agotadas, exigiendo espera positiva sin lanzamientos ante marcas reales históricas de 3600 segundos. Se ajustan las antiguas excepciones al contrato explícito; no se eliminan escenarios. |
| test_arnes_ausente | Conserva recuperación real y ausencia de ejecutable como causas distintas. Usa respuesta de 58 minutos más margen existente de 120 segundos y monotonic fijo, sin simular el parser. Las aserciones de 3600/2700 segundos admiten el contexto adicional de espera mediante ANY. |
| test_fallos_arnes | Ajusta espera supuesta 1800 a 300 y admite contexto opcional mediante ANY en las dos llamadas afectadas. Conserva las comprobaciones de cuota frente a fallos operacionales y recuperación de perfiles omitidos. |
| test_estado_agentes | Ajusta expectativas de espera/marcas sin hora a 300, conservando orden y persistencia por modelo. |
| tests/test_orquestar | Ajusta las dos expectativas autorizadas a 300 y admite contexto adicional. El test de reanudación avanza el reloj fijo durante la espera simulada y conserva su observable de reanudación de sesión. |

ANY se limita al contexto añadido; no elimina las comprobaciones de tiempo, número de esperas ni resultado. La lógica de recuperación del contexto se ejercita a través del bucle real en las regresiones nuevas.

## Regresiones nuevas

- **C1:** test_reset_entre_lecturas_no_rompe_seleccion_ni_informe captura filas reales, agrega un evento de recuperación y devuelve la instantánea anterior. Recorre selección e informe. No fabrica el resultado de selección ni el informe; un acceso incoherente entre lecturas produce error. La comprobación no depende de planificar dos procesos reales.
- **C2:** test_reset_antes_de_entrar_en_espera_no_duerme ejecuta la transición real del bucle; un callback del aviso recupera el par después de calcular el plazo. Cualquier sleep falla explícitamente. Conserva el caso separado de reset durante sleep, con comprobaciones de máximo 30 segundos y limpieza de ESPERA.
- **C3:** test_creditos_antiguos_no_suprimen_aviso_real_ajeno prepara una sospecha de créditos vencida de codex/m1 y una respuesta de reinicio real de claude/m2. Exige exactamente un aviso genérico de cuota. La espera se simula para verificar el aviso sin dormir.

## Evidencia reutilizada

Registros --verificar de orquestar_evidencias.jsonl; árbol actual de entrada **9b62e379a8a402c89f2f16b8768da49820133d29**, todos con código 0:

| Registro | Verificación |
| --- | --- |
| 10:08:08 | test_arnes_ausente.py; test_fallos_arnes.py; test_*cuota*.py |
| 10:08:09 | Dos tests específicos de tests.test_orquestar: reanudación de sesión y cuota del subagente |
| 10:09:04 | Compilación de TODOS los siete Python modificados |
| 10:09:05 | git diff --check |
| 10:09:20 | test_informe_agentes.py |
| 10:09:30 | test_estado_agentes.py |

El invocador comunica 19 tests de cuota, 9 de arnés ausente y 14 de fallos de arnés. Se acepta esa evidencia sin recontarla. La ejecución completa de tests.test_orquestar se está renovando; no se le atribuye un verde actual ni se reutiliza un verde anterior como si perteneciera a este árbol.

Fase roja de C1–C3: test_cuota_supuesta.py, 10:07:11, árbol 079ff01b3590ace2b1ff80eae545cbe723423e8e, código 1. Detalle aportado: 11 métodos, dos errores KeyError y dos fallos, propios de los defectos; verde posterior a las 10:07:41 en 821c5ddf3bb23b07c429717bf9bd2c2216df51cf y también cubierto por el patrón de cuota en el árbol actual. Se conserva además la fase roja original anterior a implementar --cuota-reset y reset_cuotas.

No se ejecutaron pruebas, compilación, diff --check ni suite completa. No hay lint ni tipado configurados. Se consultaron directamente las evidencias ya registradas con --verificar.

## Puntuaciones

| Dimensión | Nota | Motivo |
| --- | --- | --- |
| Cobertura | 9/10 | Delta completo, escenarios aprobados y regresiones concretas de C1–C3. |
| Aserciones | 9/10 | Selección, límites, persistencia, salidas y avisos observables; el reset previo discrimina cualquier espera efectiva. |
| Rojo correcto | 9/10 | Rojo funcional registrado y estímulos que reproducen las carencias; ajuste temporal del fixture de reanudación coherente con el contrato. |
| Estabilidad | 9/10 | Relojes y procesos simulados, JSONL temporal real e intercalados controlados, sin concurrencia azarosa. |

**Media: 9/10.** Sin hallazgos críticos ni altos.

## Seguimiento y salida

| Hallazgo anterior | Dictamen y enrutado |
| --- | --- |
| T1 — ALTA: estado y hora visible | Resuelto; se mantiene. Consultas CLI de ambos informes con deducción real de estado, hora y clasificación/origen; seleccionados/ajenos tras reset. para: desarrollador; destino: resolver, completado. |
| T2 — ALTA: segundo fallo de créditos | Resuelto; se mantiene. Secuencias codex/claude, reserva sola a 299, titular a 300 y tras reset para las tres cadenas; aviso único y nuevo episodio. para: desarrollador; destino: resolver, completado. |
| T3 — MEDIA: recuperación persistida e histórico | Resuelto; se mantiene. Eventos por pares y prefijo intacto, incluido histórico de 3600. para: desarrollador; destino: resolver, completado. |

Hallazgos nuevos de pruebas: ninguno. **APROBADO.** No quedan acciones de review-test. Este veredicto permite review-code y no cierra el bug ni certifica una ejecución completa final de tests.test_orquestar.
