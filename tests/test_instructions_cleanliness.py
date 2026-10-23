"""Pruebas de limpieza y ausencia de rutas prohibidas en instrucciones distribuibles.

Verifica CA-M-3 (@CA-F02-04, @RF-F02-05):
Ningún archivo de instrucciones del contenido distribuible (skills/** salvo .py,
agents/**, workflows/**, skills/release/templates/RELEASING.md) debe contener
rutas relativas que empiecen por .agents/, invocaciones python .../*.py,
referencias a skills/<nombre>/scripts ni rutas relativas ../.
"""

import os
import re
import unittest
from pathlib import Path


class TestInstructionsCleanliness(unittest.TestCase):
    """Audita los archivos de instrucciones distribuibles contra patrones prohibidos."""

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.forbidden_patterns = {
            "dot_agents": re.compile(r"\.agents/"),
            "python_script": re.compile(r"python\s+[\w\-\./\\<>]+\.py"),
            "skills_scripts": re.compile(r"skills/[\w\-<>]+/scripts"),
            "dotdot_slash": re.compile(r"\.\./"),
        }

    def _get_distributable_instruction_files(self):
        targets = ["skills", "agents", "workflows"]
        files_to_check = []
        for t in targets:
            folder = self.root / t
            if not folder.exists():
                continue
            for p in folder.rglob("*"):
                if p.is_file():
                    # Excluir código fuente de scripts o bytecode Python
                    if p.suffix in (".py", ".pyc"):
                        continue
                    files_to_check.append(p)
        return files_to_check

    def test_ca_f02_04_no_forbidden_patterns_in_instructions(self):
        """CA-M-3: Ningún archivo de instrucciones contiene .agents/, python *.py, skills/*/scripts ni ../."""
        files = self._get_distributable_instruction_files()
        self.assertGreater(len(files), 0, "No se encontraron archivos de instrucciones para auditar")

        hallazgos = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                self.fail(f"No se pudo leer {file_path}: {e}")

            rel_path = file_path.relative_to(self.root).as_posix()
            for rule_name, pattern in self.forbidden_patterns.items():
                for match in pattern.finditer(content):
                    snippet = content[max(0, match.start() - 25):min(len(content), match.end() + 25)].replace("\n", " ")
                    hallazgos.append(f"[{rule_name}] {rel_path}: '{match.group(0)}' en contexto: '...{snippet}...'")

        if hallazgos:
            mensaje = f"Se detectaron {len(hallazgos)} coincidencias de patrones prohibidos:\n" + "\n".join(hallazgos)
            self.fail(mensaje)


if __name__ == "__main__":
    unittest.main()
