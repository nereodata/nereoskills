"""Regresiones de los ajustes transversales de v1.0 (B-ADV-0022)."""
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from skills.orquestar import orquestar


class AjustesTransversalesTests(unittest.TestCase):
    """Cubre la salida de verificaciones, el frontmatter y el motivo de espera."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_verificar_no_copia_la_salida_en_las_metricas(self):
        with patch.object(orquestar, 'arbol', return_value='a' * 40), patch.object(orquestar, 'excluir'), \
                patch.object(orquestar.subprocess, 'run', return_value=subprocess.CompletedProcess('', 0)):
            orquestar.verificar(self.root, 'comando')
        metricas = [json.loads(l) for l in (self.root / orquestar.METRICAS).read_text(encoding='utf-8').splitlines()]
        evidencias = [json.loads(l) for l in (self.root / orquestar.EVIDENCIAS).read_text(encoding='utf-8').splitlines()]
        self.assertNotIn('salida', metricas[-1])
        self.assertIn('salida', evidencias[-1])

    def test_reescribir_frontmatter_actualiza_y_anade_claves(self):
        texto = '---\nid: B-1\nstatus: planned\n---\n\ncuerpo\n'
        cabecera, cuerpo = orquestar.reescribir_frontmatter(texto, {'status': 'blocked', 'pendiente_de': 'humano'})
        self.assertEqual(cabecera, '---\nid: B-1\nstatus: blocked\npendiente_de: humano')
        self.assertEqual(cuerpo.strip(), 'cuerpo')

    def test_espera_conserva_el_motivo_para_el_estado(self):
        hasta = datetime.now() + timedelta(minutes=30)
        (self.root / orquestar.ESPERA).write_text(
            f"{hasta.isoformat(timespec='minutes')}\nfallo del arnés", encoding='utf-8')
        fin, motivo = orquestar.leer_espera(self.root)
        self.assertEqual(motivo, 'fallo del arnés')
        self.assertIsNotNone(fin)

    def test_espera_antigua_sin_motivo_es_de_cuota(self):
        (self.root / orquestar.ESPERA).write_text('2026-10-23T12:15:00+00:00', encoding='utf-8')
        self.assertEqual(orquestar.leer_espera(self.root)[1], 'sin cuota')


if __name__ == '__main__':
    unittest.main()
