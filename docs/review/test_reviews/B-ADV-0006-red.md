# Evidencia roja · B-ADV-0006

Ejecuciones mediante `adevv orquestar --verificar`, limitadas a `SuiteRecoveryTests`. Las salidas completas locales permanecen en `.git/`.

## Antes de implementar recuperación

```text
ERROR: test_blocked_and_cancelled_are_not_reopened (test_orquestar.SuiteRecoveryTests.test_blocked_and_cancelled_are_not_reopened)
AttributeError: module 'orquestar' has no attribute 'registrar_fallo_suite'
ERROR: test_capture_and_green_reuse_keep_return_contract (test_orquestar.SuiteRecoveryTests.test_capture_and_green_reuse_keep_return_contract)
KeyError: 'salida'
ERROR: test_capture_is_bounded_and_retains_last_error (test_orquestar.SuiteRecoveryTests.test_capture_is_bounded_and_retains_last_error)
KeyError: 'salida'
ERROR: test_loop_at_maximum_notifies_and_never_launches_review (test_orquestar.SuiteRecoveryTests.test_loop_at_maximum_notifies_and_never_launches_review)
AttributeError: module 'orquestar' has no attribute 'registrar_fallo_suite'
ERROR: test_maximum_stops_after_three_failed_fixes_with_last_output (test_orquestar.SuiteRecoveryTests.test_maximum_stops_after_three_failed_fixes_with_last_output)
AttributeError: module 'orquestar' has no attribute 'registrar_fallo_suite'
ERROR: test_pending_recheck_does_not_count_another_fix_or_duplicate (test_orquestar.SuiteRecoveryTests.test_pending_recheck_does_not_count_another_fix_or_duplicate)
AttributeError: module 'orquestar' has no attribute 'registrar_fallo_suite'
ERROR: test_recurrences_reuse_bug_preserve_work_and_promote_after_three (test_orquestar.SuiteRecoveryTests.test_recurrences_reuse_bug_preserve_work_and_promote_after_three)
AttributeError: module 'orquestar' has no attribute 'registrar_fallo_suite'
ERROR: test_registration_uses_configured_path_prefix_and_normal_selection (test_orquestar.SuiteRecoveryTests.test_registration_uses_configured_path_prefix_and_normal_selection)
AttributeError: module 'orquestar' has no attribute 'registrar_fallo_suite'
FAIL: test_loop_runs_bug_fix_then_green_suite_then_review (test_orquestar.SuiteRecoveryTests.test_loop_runs_bug_fix_then_green_suite_then_review)
AssertionError: Lists differ: [] != ['bug-fix', 'revisar-version']
Ran 9 tests in 6.530s
FAILED (failures=1, errors=8)
```

## Regresiones de los hallazgos de QA

```text
FAIL: test_escaped_command_reuses_id_without_pyyaml (test_orquestar.SuiteRecoveryTests.test_escaped_command_reuses_id_without_pyyaml)
AssertionError: 'B-DEM-0002' != 'B-DEM-0001'
FAIL: test_long_stop_output_fits_final_telegram_transport (test_orquestar.SuiteRecoveryTests.test_long_stop_output_fits_final_telegram_transport)
AssertionError: 10133 not less than or equal to 4096
Ran 14 tests in 23.596s
FAILED (failures=2)
```

La ausencia de `registrar_fallo_suite` y `salida`, y la lista vacía de pasos, muestran el contrato anterior. El rojo de QA produce otro ID con el mismo comando escapado y un mensaje de 10133 unidades UTF-16; ambos son fallos funcionales, con fixtures operativos.
