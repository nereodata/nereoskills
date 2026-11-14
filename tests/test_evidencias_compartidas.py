"""Pruebas de regresión del circuito unificado de evidencias y árbol (B-ADV-0031)."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from skills.orquestar import chequeos, orquestar


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


class EvidenciasCompartidasTests(unittest.TestCase):
    """Cubre los escenarios @B-ADV-0031 de tests/features/publicacion.feature."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self._repo_counter = 0

    def _crear_repo_con_worktree(self, entradas_pruebas=None):
        self._repo_counter += 1
        raiz_caso = self.base / f"caso_{self._repo_counter}"
        repo = raiz_caso / "principal"
        repo.mkdir(parents=True, exist_ok=True)
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.email", "test@adevv.local")
        _git(repo, "config", "user.name", "Test Adevv")

        (repo / "src").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "precios.py").write_text("PRECIO = 10\n", encoding="utf-8")
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        cmd_ok = f'"{sys.executable}" -c "print(\'ok-b-adv-0031\')"'
        cmd_yaml = json.dumps(cmd_ok)
        if entradas_pruebas:
            bloque_pruebas = f"  pruebas:\n    comando: {cmd_yaml}\n    obligatorio: true\n    entradas:\n" + "".join(
                f"      - {e}\n" for e in entradas_pruebas
            )
        else:
            bloque_pruebas = f"  pruebas: {cmd_yaml}\n"
        (repo / "task_config.yaml").write_text(
            f"validation:\n  command: {cmd_yaml}\n{bloque_pruebas}"
            "release:\n"
            "  puertas:\n"
            "    - pruebas\n"
            "  preflight:\n"
            f"    - {cmd_yaml}\n",
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "chore: inicial")

        secundario = raiz_caso / "secundario"
        _git(repo, "worktree", "add", "--detach", str(secundario), "HEAD")
        self.addCleanup(
            lambda: subprocess.run(
                ["git", "worktree", "remove", "--force", str(secundario)],
                cwd=repo,
                capture_output=True,
            )
        )
        return repo, secundario, cmd_ok

    def test_orquestar_delega_arbol_verificar_y_mandato_en_chequeos(self):
        repo, _, cmd_ok = self._crear_repo_con_worktree()
        with patch.object(chequeos, "arbol_trabajo", wraps=chequeos.arbol_trabajo) as spy_arbol:
            clave = orquestar.arbol(repo)
            self.assertEqual(spy_arbol.call_count, 1)
            self.assertRegex(clave, r"^[0-9a-f]{40}([0-9a-f]{24})?$")

        with patch.object(chequeos, "verificar_comando", wraps=chequeos.verificar_comando) as spy_verif:
            rc = orquestar.verificar(repo, cmd_ok)
            self.assertEqual(rc, 0)
            self.assertEqual(spy_verif.call_count, 1)

        with patch.object(
            chequeos, "comandos_verificados_arbol", wraps=chequeos.comandos_verificados_arbol
        ) as spy_cmds:
            prompt = orquestar.construir_prompt_agente(repo, "hades", "Ejecuta /review-code.")
            self.assertGreaterEqual(spy_cmds.call_count, 1)
            self.assertIn(cmd_ok, prompt)

    def test_evidencia_compartida_entre_entradas_y_worktrees(self):
        """Escenario: Evidencia compartida entre entradas y worktrees."""
        principal, secundario, cmd_ok = self._crear_repo_con_worktree()

        prev_principal = {
            "contrato": "v2",
            "fecha": "2026-01-01T10:00:00",
            "etapa": "pruebas",
            "comando": "python -m unittest prev_main",
            "arbol": "1" * 40,
            "identidad": "id-prev-main",
            "codigo": 0,
            "acreditado": True,
        }
        prev_secundario = {
            "contrato": "v2",
            "fecha": "2026-01-01T10:01:00",
            "etapa": "pruebas",
            "comando": "python -m unittest prev_sec",
            "arbol": "2" * 40,
            "identidad": "id-prev-sec",
            "codigo": 0,
            "acreditado": True,
        }
        (principal / chequeos.EVIDENCIAS).write_text(json.dumps(prev_principal) + "\n", encoding="utf-8")
        (secundario / chequeos.EVIDENCIAS).write_text(json.dumps(prev_secundario) + "\n", encoding="utf-8")

        buf_sec = io.StringIO()
        with redirect_stdout(buf_sec):
            rc_sec = orquestar.verificar(secundario, cmd_ok)
        self.assertEqual(rc_sec, 0)

        historial_tras_sec = chequeos.leer_evidencias(principal)
        comandos_hist = [r["comando"] for r in historial_tras_sec]
        self.assertIn("python -m unittest prev_main", comandos_hist)
        self.assertIn("python -m unittest prev_sec", comandos_hist)
        self.assertEqual(comandos_hist.count(cmd_ok), 1)
        total_antes_reuso = len(historial_tras_sec)

        buf_main = io.StringIO()
        with patch.object(chequeos, "_invocar_ejecutor") as mock_exec, redirect_stdout(buf_main):
            rc_main = orquestar.verificar(principal, cmd_ok)
            self.assertEqual(rc_main, 0)
            mock_exec.assert_not_called()

        salida_main = buf_main.getvalue()
        self.assertIn("el último resultado real fue verde para el mismo comando, entradas y entorno", salida_main)

        with patch.object(chequeos, "_invocar_ejecutor") as mock_exec_pf:
            res_pf = chequeos.ejecutar_preflight_worktree(principal)
            self.assertEqual(res_pf["estado"], "aprobado")
            mock_exec_pf.assert_not_called()
            self.assertTrue(res_pf["comandos"][0]["reutilizada"])
            self.assertIn(
                "el último resultado real fue verde para el mismo comando, entradas y entorno",
                res_pf["comandos"][0]["diagnostico"],
            )

        prompt_hades = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
        self.assertIn("Verificado en verde sobre este árbol", prompt_hades)
        self.assertIn(f"`{cmd_ok}`", prompt_hades)

        historial_final = chequeos.leer_evidencias(principal)
        self.assertEqual(len(historial_final), total_antes_reuso)

    def test_fallo_posterior_invalida_exito_compartido(self):
        """Escenario: Un fallo posterior invalida un éxito compartido."""
        principal, _, cmd_ok = self._crear_repo_con_worktree()
        cmd_segundo = f'"{sys.executable}" -c "print(\'segundo\')"'
        cmd_ok_yaml = json.dumps(cmd_ok)
        cmd_seg_yaml = json.dumps(cmd_segundo)
        (principal / "task_config.yaml").write_text(
            f"validation:\n  command: {cmd_ok_yaml}\n  pruebas: {cmd_ok_yaml}\n"
            "release:\n  puertas:\n    - pruebas\n  preflight:\n"
            f"    - {cmd_ok_yaml}\n"
            f"    - {cmd_seg_yaml}\n",
            encoding="utf-8",
        )
        _git(principal, "add", "task_config.yaml")
        _git(principal, "commit", "-m", "chore: dos comandos preflight")

        self.assertEqual(orquestar.verificar(principal, cmd_ok), 0)
        prompt_inicial = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
        self.assertIn(f"`{cmd_ok}`", prompt_inicial)

        ejecuciones_pf = []

        def ejecutor_fallo(cwd, comando):
            ejecuciones_pf.append(comando)
            return 1, "fallo simulado en preflight"

        res_pf = chequeos.ejecutar_preflight_worktree(
            principal,
            ejecutor=ejecutor_fallo,
            forzar_ejecucion=True,
        )
        self.assertEqual(res_pf["estado"], "fallido")
        self.assertIn("fallo simulado en preflight", res_pf["motivo"])
        self.assertEqual(len(ejecuciones_pf), 1)
        self.assertEqual(len(res_pf["comandos"]), 1)

        evidencias = chequeos.leer_evidencias(principal)
        self.assertEqual(evidencias[-1]["codigo"], 1)
        self.assertIn("fallo simulado en preflight", evidencias[-1]["diagnostico"])

        prompt_tras_fallo = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
        self.assertNotIn(f"`{cmd_ok}`", prompt_tras_fallo)

        buf_reintento = io.StringIO()
        with (
            patch.object(chequeos, "_invocar_ejecutor", wraps=chequeos._invocar_ejecutor) as spy_exec,
            redirect_stdout(buf_reintento),
        ):
            rc_nuevo = orquestar.verificar(principal, cmd_ok)
            self.assertEqual(rc_nuevo, 0)
            self.assertEqual(spy_exec.call_count, 1)

        self.assertIn("el último resultado falló", buf_reintento.getvalue())

    def test_evidencia_sin_identidad_acreditable_exige_ejecucion(self):
        """Esquema del escenario: Evidencia sin identidad acreditable exige ejecución."""
        for caso_entorno in ("ausente", "distinto del entorno actual"):
            with self.subTest(entorno=caso_entorno):
                principal, _, cmd_ok = self._crear_repo_con_worktree()
                clave_actual = orquestar.arbol(principal)
                _, info_etapa = chequeos._info_para_comando(principal, comando=cmd_ok)
                info_id = chequeos.calcular_identidad(principal, "pruebas", info_etapa, clave_arbol=clave_actual)

                if caso_entorno == "ausente":
                    registro_historico = {
                        "contrato": "v1",
                        "fecha": "2026-01-01T12:00:00",
                        "etapa": "pruebas",
                        "comando": cmd_ok,
                        "arbol": clave_actual,
                        "hash_contenido": info_id["hash_contenido"],
                        "codigo": 0,
                        "salida": "ok legado sin entorno",
                    }
                else:
                    entorno_distinto = dict(info_id["entorno"])
                    entorno_distinto["herramienta"] = "python-0.0.0-distinto"
                    registro_historico = {
                        "contrato": "v2",
                        "fecha": "2026-01-01T12:00:00",
                        "etapa": "pruebas",
                        "comando": cmd_ok,
                        "arbol": clave_actual,
                        "identidad": "identidad-entorno-distinto",
                        "identidad_inicial": "identidad-entorno-distinto",
                        "identidad_final": "identidad-entorno-distinto",
                        "hash_contenido": info_id["hash_contenido"],
                        "entorno": entorno_distinto,
                        "codigo": 0,
                        "acreditado": True,
                        "salida": "ok entorno distinto",
                    }

                linea_historica = json.dumps(registro_historico, ensure_ascii=False) + "\n"
                ruta_ev_local = principal / chequeos.EVIDENCIAS
                ruta_coord = chequeos.directorio_coordinacion(principal, crear=True)

                def restaurar_historial():
                    for f in ruta_coord.glob("*"):
                        if f.is_file():
                            f.unlink()
                    ruta_ev_local.write_text(linea_historica, encoding="utf-8")

                restaurar_historial()
                prompt = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
                self.assertNotIn(f"`{cmd_ok}`", prompt)

                buf_verif = io.StringIO()
                with (
                    patch.object(chequeos, "_invocar_ejecutor", wraps=chequeos._invocar_ejecutor) as spy_v,
                    redirect_stdout(buf_verif),
                ):
                    rc_v = orquestar.verificar(principal, cmd_ok)
                    self.assertEqual(rc_v, 0)
                    self.assertEqual(spy_v.call_count, 1)

                self.assertIn(caso_entorno, buf_verif.getvalue())
                evs_tras_verif = chequeos.leer_evidencias(principal)
                self.assertEqual(len(evs_tras_verif), 2)
                self.assertEqual(evs_tras_verif[0]["salida"], registro_historico["salida"])
                self.assertIn(caso_entorno, evs_tras_verif[1]["motivo_no_reutilizacion"])
                self.assertIn(caso_entorno, evs_tras_verif[1]["diagnostico"])

                restaurar_historial()
                buf_pf = io.StringIO()
                with (
                    patch.object(chequeos, "_invocar_ejecutor", wraps=chequeos._invocar_ejecutor) as spy_pf,
                    redirect_stdout(buf_pf),
                ):
                    res_pf = chequeos.ejecutar_preflight_worktree(principal)
                    self.assertEqual(res_pf["estado"], "aprobado")
                    self.assertEqual(spy_pf.call_count, 1)

                self.assertFalse(res_pf["comandos"][0]["reutilizada"])
                self.assertIn(caso_entorno, res_pf["comandos"][0]["diagnostico"])
                evs_tras_pf = chequeos.leer_evidencias(principal)
                self.assertEqual(len(evs_tras_pf), 2)
                self.assertEqual(evs_tras_pf[0]["salida"], registro_historico["salida"])
                self.assertIn(caso_entorno, evs_tras_pf[1]["motivo_no_reutilizacion"])

    def test_comando_modifica_entradas_durante_ejecucion(self):
        """Escenario: Un comando modifica sus entradas durante la ejecución."""
        principal, _, _ = self._crear_repo_con_worktree(entradas_pruebas=["src/precios.py"])
        cmd_mutador = (
            f'"{sys.executable}" -c '
            "\"from pathlib import Path; p = Path('src/precios.py'); "
            "p.write_text(p.read_text(encoding='utf-8') + '# mutado\\n', encoding='utf-8')\""
        )

        rc1 = orquestar.verificar(principal, cmd_mutador)
        self.assertEqual(rc1, 0)

        evidencias = chequeos.leer_evidencias(principal)
        self.assertEqual(len(evidencias), 1)
        ultima = evidencias[-1]
        self.assertTrue(ultima["cambio_en_vuelo"])
        self.assertFalse(ultima["acreditado"])
        self.assertIsNotNone(ultima["identidad_inicial"])
        self.assertIsNotNone(ultima["identidad_final"])
        self.assertNotEqual(ultima["identidad_inicial"], ultima["identidad_final"])

        prompt_hades = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
        self.assertNotIn("Verificado en verde sobre este árbol", prompt_hades)

        with patch.object(chequeos, "_invocar_ejecutor", wraps=chequeos._invocar_ejecutor) as spy_exec:
            rc2 = orquestar.verificar(principal, cmd_mutador)
            self.assertEqual(rc2, 0)
            self.assertEqual(spy_exec.call_count, 1)

    def test_preflight_espera_comprobacion_equivalente_en_otro_worktree(self):
        """Esquema del escenario: El preflight espera la comprobación equivalente iniciada en otro worktree."""
        for codigo_esperado, palabra_resultado, acredita in (
            (0, "éxito", True),
            (1, "fallo", False),
        ):
            with self.subTest(codigo=codigo_esperado):
                principal, secundario, cmd_ok = self._crear_repo_con_worktree()

                evento_en_ejecucion = threading.Event()
                evento_liberar = threading.Event()
                llamadas_reales = []

                def ejecutor_lento(comando, root=None, **kw):
                    llamadas_reales.append((Path(root or secundario).resolve(), comando))
                    evento_en_ejecucion.set()
                    evento_liberar.wait(timeout=10)
                    return codigo_esperado, f"diagnóstico compartido código {codigo_esperado}"

                res_verificar = {}
                res_preflight = {}
                buf_pf = io.StringIO()

                def hilo_verificar():
                    res_verificar["res"] = chequeos.verificar_comando(
                        secundario,
                        cmd_ok,
                        ejecutor=ejecutor_lento,
                    )

                t_verif = threading.Thread(target=hilo_verificar)
                t_verif.start()
                self.assertTrue(evento_en_ejecucion.wait(timeout=5))

                coord_key = (
                    str(chequeos.directorio_coordinacion(principal, crear=False).resolve()),
                    cmd_ok,
                )
                with chequeos._LOCK_GLOBAL:
                    evento_esperando = chequeos._EJECUCIONES_MEMORIA[coord_key]["evento_esperando"]

                def hilo_preflight():
                    with redirect_stdout(buf_pf):
                        res_preflight["res"] = chequeos.ejecutar_preflight_worktree(
                            principal,
                            ejecutor=ejecutor_lento,
                        )

                t_pf = threading.Thread(target=hilo_preflight)
                t_pf.start()
                self.assertTrue(evento_esperando.wait(timeout=5))

                prompt_en_vuelo = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
                self.assertNotIn(f"`{cmd_ok}`", prompt_en_vuelo)

                evento_liberar.set()
                t_verif.join(timeout=5)
                t_pf.join(timeout=5)

                salida_pf = buf_pf.getvalue()
                self.assertIn("espera el resultado de la comprobación equivalente en curso", salida_pf)
                self.assertIn(palabra_resultado, salida_pf)
                self.assertIn(f"diagnóstico compartido código {codigo_esperado}", salida_pf)

                pf_cmd = res_preflight["res"]["comandos"][0]
                self.assertTrue(pf_cmd.get("espero_en_curso"))
                self.assertEqual(pf_cmd.get("resultado_compartido"), palabra_resultado)
                self.assertIn(f"diagnóstico compartido código {codigo_esperado}", pf_cmd.get("diagnostico", ""))

                self.assertEqual(len(llamadas_reales), 1)
                evidencias = chequeos.leer_evidencias(principal)
                self.assertEqual(len(evidencias), 1)

                prompt_final = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
                if acredita:
                    self.assertIn(f"`{cmd_ok}`", prompt_final)
                else:
                    self.assertNotIn(f"`{cmd_ok}`", prompt_final)

    def test_edicion_previa_invalida_exito_con_entorno_estable(self):
        """Esquema del escenario: Una edición previa invalida el éxito aunque el entorno siga igual."""
        for entrada in ("verificar", "preflight"):
            with self.subTest(entrada=entrada):
                principal, _, cmd_ok = self._crear_repo_con_worktree(entradas_pruebas=["src/precios.py"])

                self.assertEqual(orquestar.verificar(principal, cmd_ok), 0)
                ev_previa = chequeos.leer_evidencias(principal)
                self.assertEqual(len(ev_previa), 1)
                hash_previo = ev_previa[0]["hash_contenido"]

                (principal / "src" / "precios.py").write_text("PRECIO = 25\n", encoding="utf-8")

                prompt_antes = orquestar.construir_prompt_agente(principal, "hades", "Ejecuta /review-code.")
                self.assertNotIn(f"`{cmd_ok}`", prompt_antes)

                buf = io.StringIO()
                with (
                    patch.object(chequeos, "_invocar_ejecutor", wraps=chequeos._invocar_ejecutor) as spy_exec,
                    redirect_stdout(buf),
                ):
                    if entrada == "verificar":
                        rc = orquestar.verificar(principal, cmd_ok)
                        self.assertEqual(rc, 0)
                    else:
                        res_pf = chequeos.ejecutar_preflight_worktree(principal)
                        self.assertEqual(res_pf["estado"], "aprobado")
                        self.assertIn("cambio de entradas", res_pf["comandos"][0]["diagnostico"])
                    self.assertEqual(spy_exec.call_count, 1)

                self.assertIn("cambio de entradas", buf.getvalue())
                ev_final = chequeos.leer_evidencias(principal)
                self.assertEqual(len(ev_final), 2)
                self.assertEqual(ev_final[0]["hash_contenido"], hash_previo)
                self.assertEqual(ev_final[0]["codigo"], 0)
                self.assertNotEqual(ev_final[1]["hash_contenido"], hash_previo)
                self.assertIn("cambio de entradas", ev_final[1]["diagnostico"])


if __name__ == "__main__":
    unittest.main()
