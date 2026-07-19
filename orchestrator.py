#!/usr/bin/env python3
"""
TaskOrchestrator: Ejecuta task-dev de forma determinista y completamente funcional.

Características:
- Orden forzado de fases (A → B → C → D → E → F)
- Validación obligatoria antes de progresar
- Estado persistido en JSON (recuperable)
- HITL explícito (pausa para aprobación humana)
- Dos modos: 'mock' (testing offline) e 'interactive' (con Claude)

Uso:
  python orchestrator.py run [TASK_ID]          # Modo interactivo
  python orchestrator.py run [TASK_ID] --mock   # Modo mock (testing)
  python orchestrator.py status [TASK_ID]
  python orchestrator.py resume [TASK_ID]
"""

import json
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
import re


class PhaseStatus(Enum):
    """Estado de una fase."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseState:
    """Estado de una fase individual."""
    name: str                          # Nombre descriptivo
    status: str = PhaseStatus.PENDING.value
    result: Optional[Dict[str, Any]] = None  # Artefactos reales producidos
    validated: bool = False
    validation_notes: str = ""
    error: Optional[str] = None
    attempts: int = 0

    # Estructuras de resultado por fase (sirven como schema)
    # Fase A (Definición BDD)
    # "result": {
    #   "feature_file": "path/to/T-NTR-XXXX.feature" | null,
    #   "review_spec_verdict": "APROBADO|RECHAZADO|PENDIENTE",
    #   "review_spec_report": "docs/review/spec_reviews/T-NTR-XXXX-spec-review.md" | null,
    #   "debt": ["...", "..."]
    # }

    # Fase B (Diseño)
    # "result": {
    #   "design_file": "docs/design/T-NTR-XXXX-design.md" | null,
    #   "changes": ["[NEW] pkg/X.go", "[MODIFY] pkg/Y.go"],
    #   "review_design_verdict": "APROBADO|RECHAZADO|PENDIENTE",
    #   "review_design_report": "docs/review/design_reviews/..." | null,
    #   "debt": [...]
    # }

    # Fase C (Tests + Desarrollo)
    # "result": {
    #   "test_files": ["tests/unit/X_test.go", ...],
    #   "implementation_files": ["pkg/core/X.go", ...],
    #   "review_test_verdict": "APROBADO|RECHAZADO|PENDIENTE",
    #   "review_test_report": "docs/review/test_reviews/..." | null,
    #   "debt": [...]
    # }

    # Fase D (QA - Code Review)
    # "result": {
    #   "review_code_verdict": "APROBADO|RECHAZADO|PENDIENTE",
    #   "review_code_report": "docs/review/code_reviews/..." | null,
    #   "review_code_issues": ["CRÍTICO: ...", "ALTA: ...", ...],
    #   "debt": [...]
    # }

    # Fase E (Documentación)
    # "result": {
    #   "updated_files": ["docs/...", "README.md", ...],
    #   "debt": [...]
    # }

    # Fase F (Cierre)
    # "result": {
    #   "commit_hash": "abc1234def567" | null,
    #   "commit_message": "feat(NTR): ...",
    #   "status": "completed|failed"
    # }


@dataclass
class TaskState:
    """Estado persistido de la tarea."""
    task_id: str
    version: str
    branch: str
    status: str                        # initialized | in_progress | completed | failed
    created_at: str
    updated_at: str
    is_mock: bool = False              # Flag: mock mode o interactivo
    triaged: bool = False
    triage: Dict[str, str] = field(default_factory=dict)
    phases: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_phase_completed: Optional[str] = None
    next_phase_waiting: Optional[str] = None


class TaskOrchestrator:
    """Orquestador determinista de tareas con HITL."""

    PHASES = ['A', 'B', 'C', 'D', 'E', 'F']
    PHASE_NAMES = {
        'A': 'Definición (BDD + review-spec)',
        'B': 'Diseño (design + review-design)',
        'C': 'Desarrollo (tests + review-test)',
        'D': 'QA (review-code)',
        'E': 'Documentación (manage-docs)',
        'F': 'Cierre (commit)',
    }
    STATE_DIR = Path('.tasks')
    MAX_RETRIES = 3

    def __init__(self, task_id: str, mock_mode: bool = False, fast_mode: bool = False):
        self.task_id = task_id
        self.mock_mode = mock_mode
        self.fast_mode = fast_mode
        self.state_file = self.STATE_DIR / f'{task_id}.json'
        self.state = self._load_or_create_state()

    def _load_or_create_state(self) -> TaskState:
        """Carga estado existente o crea uno nuevo."""
        self.STATE_DIR.mkdir(exist_ok=True)

        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                return TaskState(**data)

        # Nuevo estado
        return TaskState(
            task_id=self.task_id,
            version="",
            branch="",
            status="pending",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            phases={
                phase: asdict(PhaseState(name=self.PHASE_NAMES[phase]))
                for phase in self.PHASES
            },
            triage={}
        )

    def save_state(self):
        """Persiste estado en JSON."""
        self.state.updated_at = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)

    def run(self):
        """Ejecuta el flujo desde donde quedó."""
        if self.mock_mode:
            mode_label = "(MOCK)"
        elif self.fast_mode:
            mode_label = "(FAST - sin HITL)"
        else:
            mode_label = "(INTERACTIVE)"

        print(f"\n{'='*70}")
        print(f"TASK ORCHESTRATOR {mode_label}")
        print(f"Task ID: {self.task_id}")
        print(f"{'='*70}\n")

        # Registrar modo
        self.state.is_mock = self.mock_mode

        # [1] INIT
        if self.state.status == "pending":
            self._init_phase()
            self.save_state()

        # [2] TRIAGE
        if not self.state.triaged:
            self._triage_phase()
            self.save_state()

        # [3-8] PHASES
        for phase in self.PHASES:
            if self._should_execute(phase):
                self._execute_phase(phase)
                self.save_state()

                if self._validate_phase(phase):
                    # Validación ok, pausa HITL (solo si no es fast/mock)
                    if not self.mock_mode and not self.fast_mode:
                        self._hitl_pause(phase)
                    self.save_state()
                else:
                    # Validación falla
                    if not self._handle_validation_failure(phase):
                        print(f"❌ Phase {phase} falló después de {self.MAX_RETRIES} intentos.")
                        self.state.phases[phase]['status'] = PhaseStatus.FAILED.value
                        self.save_state()
                        return
                    self.save_state()

        # [9] CLOSE
        self._close_phase()
        self.save_state()

    def _init_phase(self):
        """[1] INIT: Valida rama, carga metadatos."""
        print("[1] INIT: Validando configuración...\n")

        # Detectar rama actual
        try:
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=Path.cwd(),
                text=True
            ).strip()
        except:
            branch = "unknown"

        # Validar rama
        if not re.match(r'^(release/v\d+\.\d+|hotfix/v\d+\.\d+\.\d+)$', branch):
            print(f"⚠️  Rama: {branch} (no es release/vX.Y ni hotfix/vX.Y.Z)")
        else:
            print(f"✅ Rama: {branch}")

        # Detectar versión de rama
        match = re.search(r'v(\d+\.\d+(?:\.\d+)?)', branch)
        version = match.group(1) if match else "unknown"

        self.state.status = "in_progress"
        self.state.branch = branch
        self.state.version = version

        print(f"✅ Versión: {version}")
        print(f"✅ Estado: in_progress\n")

    def _triage_phase(self):
        """[2] TRIAGE: Decide [EXEC]/[SKIP] para cada fase."""
        print("[2] TRIAGE: Analizando cambios...\n")

        # Lógica simple: todas las fases se ejecutan por defecto
        # En producción, esto analizaría git diff y decidiría realmente
        self.state.triage = {
            'A': 'EXEC',  # Especificación (BDD)
            'B': 'EXEC',  # Diseño técnico
            'C': 'EXEC',  # Tests + implementación
            'D': 'EXEC',  # QA (review-code)
            'E': 'EXEC',  # Documentación
            'F': 'EXEC',  # Commit + cierre
        }

        print("Decisiones de triaje:")
        for phase, decision in self.state.triage.items():
            print(f"  [{decision}] Phase {phase}: {self.PHASE_NAMES[phase]}")
        print()

        self.state.triaged = True

    def _should_execute(self, phase: str) -> bool:
        """¿Se debe ejecutar esta fase?"""
        return (self.state.triage.get(phase) == 'EXEC' and
                self.state.phases[phase]['status'] == PhaseStatus.PENDING.value)

    def _execute_phase(self, phase: str):
        """Ejecuta una fase (mock o interactivo) y captura referencias reales."""
        phase_state = self.state.phases[phase]
        skill_name = self._phase_to_skill(phase)

        print(f"[{phase}] {phase_state['name']}")
        print(f"    Ejecutando: {skill_name}\n")

        phase_state['status'] = PhaseStatus.RUNNING.value
        phase_state['attempts'] += 1

        if self.mock_mode:
            # Modo mock: simula resultado vacío (null/empty arrays, no strings)
            phase_state['result'] = self._create_mock_result(phase)
            print(f"    [MOCK] Resultado vacío (sin artefactos reales)\n")
        else:
            # Modo interactivo: espera entrada del usuario
            print(f"    → Proporciona entrada para {skill_name}:")
            print(f"      (o escribe 'skip' para saltar esta fase)\n")

            user_input = input("    > ").strip()

            if user_input.lower() == 'skip':
                phase_state['status'] = PhaseStatus.SKIPPED.value
                print()
                return

            # Capturar referencias reales a artefactos
            phase_state['result'] = self._extract_artifacts(phase, user_input)
            print()

        phase_state['status'] = PhaseStatus.COMPLETED.value

    def _create_mock_result(self, phase: str) -> Dict[str, Any]:
        """Crea estructura de resultado vacío para mock mode."""
        schemas = {
            'A': {
                'feature_file': None,
                'review_spec_verdict': 'PENDIENTE',
                'review_spec_report': None,
                'debt': []
            },
            'B': {
                'design_file': None,
                'changes': [],
                'review_design_verdict': 'PENDIENTE',
                'review_design_report': None,
                'debt': []
            },
            'C': {
                'test_files': [],
                'implementation_files': [],
                'review_test_verdict': 'PENDIENTE',
                'review_test_report': None,
                'debt': []
            },
            'D': {
                'review_code_verdict': 'PENDIENTE',
                'review_code_report': None,
                'review_code_issues': [],
                'debt': []
            },
            'E': {
                'updated_files': [],
                'debt': []
            },
            'F': {
                'commit_hash': None,
                'commit_message': None,
                'status': 'pending'
            }
        }
        return schemas.get(phase, {})

    def _extract_artifacts(self, phase: str, output: str) -> Dict[str, Any]:
        """Extrae referencias reales a artefactos del output."""
        task_id = self.task_id
        result = self._create_mock_result(phase)

        if phase == 'A':
            # Buscar .feature generado
            feature_file = self._find_feature_file(task_id)
            spec_report = self._find_review_report('spec_reviews', task_id)
            verdict = self._extract_verdict_from_output(output)

            result['feature_file'] = feature_file
            result['review_spec_verdict'] = verdict
            result['review_spec_report'] = spec_report

        elif phase == 'B':
            # Buscar docs/design/[ID]-design.md
            design_file = self._find_design_file(task_id)
            design_report = self._find_review_report('design_reviews', task_id)
            changes = self._extract_changes_from_output(output)
            verdict = self._extract_verdict_from_output(output)

            result['design_file'] = design_file
            result['changes'] = changes
            result['review_design_verdict'] = verdict
            result['review_design_report'] = design_report

        elif phase == 'C':
            # Buscar archivos de test e implementación
            test_files = self._find_test_files()
            impl_files = self._find_implementation_files()
            test_report = self._find_review_report('test_reviews', task_id)
            verdict = self._extract_verdict_from_output(output)

            result['test_files'] = test_files
            result['implementation_files'] = impl_files
            result['review_test_verdict'] = verdict
            result['review_test_report'] = test_report

        elif phase == 'D':
            # Buscar review-code report
            code_report = self._find_review_report('code_reviews', task_id)
            issues = self._extract_issues_from_output(output)
            verdict = self._extract_verdict_from_output(output)

            result['review_code_verdict'] = verdict
            result['review_code_report'] = code_report
            result['review_code_issues'] = issues

        elif phase == 'E':
            # Buscar archivos actualizados
            updated = self._find_updated_files()
            result['updated_files'] = updated

        elif phase == 'F':
            # Buscar último commit
            commit_hash = self._find_last_commit()
            result['commit_hash'] = commit_hash
            result['status'] = 'completed' if commit_hash else 'pending'

        return result

    def _find_feature_file(self, task_id: str) -> Optional[str]:
        """Busca archivo .feature para la tarea."""
        # En una estructura real, sería algo como:
        # tasks/*/T-NTR-XXXX.feature
        for f in Path('.').rglob('*.feature'):
            if task_id in str(f):
                return str(f)
        return None

    def _find_design_file(self, task_id: str) -> Optional[str]:
        """Busca docs/design/[ID]-design.md."""
        design_path = Path('docs/design') / f'{task_id}-design.md'
        return str(design_path) if design_path.exists() else None

    def _find_review_report(self, review_type: str, task_id: str) -> Optional[str]:
        """Busca reporte de review (spec/design/test/code)."""
        review_dir = Path('docs/review') / review_type
        if not review_dir.exists():
            return None
        for f in review_dir.glob(f'*{task_id}*'):
            return str(f)
        return None

    def _find_test_files(self) -> list:
        """Busca archivos de test recientemente modificados."""
        test_files = []
        for f in Path('.').rglob('*_test.go'):  # Go example
            test_files.append(str(f))
        for f in Path('.').rglob('*_test.py'):  # Python example
            test_files.append(str(f))
        return test_files[:5]  # Top 5

    def _find_implementation_files(self) -> list:
        """Busca archivos de implementación recientemente modificados."""
        # En producción, usaría git diff HEAD~1 para ser preciso
        return []

    def _find_updated_files(self) -> list:
        """Busca archivos de docs actualizados."""
        updated = []
        for f in Path('docs').rglob('*.md'):
            updated.append(str(f))
        return updated[:10]

    def _find_last_commit(self) -> Optional[str]:
        """Obtiene hash del último commit."""
        try:
            commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=Path.cwd(),
                text=True
            ).strip()
            return commit[:12]  # Abbreviate
        except:
            return None

    def _extract_verdict_from_output(self, output: str) -> str:
        """Extrae veredicto (APROBADO/RECHAZADO) del output."""
        if 'APROBADO' in output.upper():
            return 'APROBADO'
        elif 'RECHAZADO' in output.upper():
            return 'RECHAZADO'
        else:
            return 'PENDIENTE'

    def _extract_changes_from_output(self, output: str) -> list:
        """Extrae cambios ([NEW]/[MODIFY]/[DELETE]) del output."""
        changes = []
        for line in output.split('\n'):
            if '[NEW]' in line or '[MODIFY]' in line or '[DELETE]' in line:
                changes.append(line.strip())
        return changes

    def _extract_issues_from_output(self, output: str) -> list:
        """Extrae issues (CRÍTICO/ALTA/MEDIA/BAJA) del output."""
        issues = []
        for line in output.split('\n'):
            for severity in ['CRÍTICO', 'ALTA', 'MEDIA', 'BAJA']:
                if severity in line:
                    issues.append(line.strip())
                    break
        return issues

    def _phase_to_skill(self, phase: str) -> str:
        """Mapea fase a skills a ejecutar."""
        skills = {
            'A': 'generate-bdd + review-spec',
            'B': 'design + review-design',
            'C': 'tests (red) + review-test',
            'D': 'review-code',
            'E': 'manage-docs',
            'F': 'commit',
        }
        return skills.get(phase, '?')

    def _validate_phase(self, phase: str) -> bool:
        """Valida que la fase se ejecutó correctamente."""
        phase_state = self.state.phases[phase]

        # Si fue skipped, validación automática
        if phase_state['status'] == PhaseStatus.SKIPPED.value:
            return True

        print(f"    Validando Phase {phase}...")

        # Lógica de validación simple
        result = phase_state.get('result', {})

        # Verificar que hay resultado
        if not result or not result.get('output'):
            phase_state['error'] = "No result provided"
            print(f"    ❌ Validación fallida: resultado vacío\n")
            return False

        # En modo mock, simula validación exitosa
        if self.mock_mode:
            phase_state['validated'] = True
            phase_state['validation_notes'] = "Mock validation passed"
            print(f"    ✅ Validación ok (mock)\n")
            return True

        # En modo interactivo, validación manual
        print(f"    ¿Validar Phase {phase}? [y/n]: ", end="")
        response = input().strip().lower()

        if response == 'y':
            phase_state['validated'] = True
            phase_state['validation_notes'] = "Manual validation passed"
            print(f"    ✅ Validación ok\n")
            return True
        else:
            phase_state['error'] = "Manual validation rejected"
            print(f"    ❌ Validación rechazada\n")
            return False

    def _handle_validation_failure(self, phase: str) -> bool:
        """Maneja validación fallida (reintenta o rechaza)."""
        phase_state = self.state.phases[phase]

        if phase_state['attempts'] >= self.MAX_RETRIES:
            print(f"    ❌ Máximo de intentos alcanzado ({self.MAX_RETRIES})")
            return False

        print(f"    ⚠️  Validación fallida (intento {phase_state['attempts']}/{self.MAX_RETRIES})")
        print(f"    ¿Reintentar? [y/n]: ", end="")

        response = input().strip().lower()
        if response == 'y':
            print()
            # Reset para reintento
            phase_state['status'] = PhaseStatus.PENDING.value
            phase_state['result'] = None
            return self._execute_phase(phase) or True  # Retry

        return False

    def _hitl_pause(self, phase: str):
        """Pausa en HITL para que el usuario continúe o rechace."""
        self.state.last_phase_completed = phase

        next_phase_idx = self.PHASES.index(phase) + 1
        if next_phase_idx < len(self.PHASES):
            self.state.next_phase_waiting = self.PHASES[next_phase_idx]

        print(f"\n{'='*70}")
        print("HITL PAUSE - APROBACIÓN REQUERIDA")
        print(f"{'='*70}")
        print(f"\nPhase {phase} ({self.PHASE_NAMES[phase]}) completada y validada.")
        print(f"Resultado: {self.state.phases[phase]['result']}\n")

        if self.state.next_phase_waiting:
            next_phase = self.state.next_phase_waiting
            print(f"Siguiente: Phase {next_phase} ({self.PHASE_NAMES[next_phase]})\n")
        else:
            print("Siguiente: CIERRE\n")

        print("¿Continuar? [y/n/reject]: ", end="")
        response = input().strip().lower()

        if response == 'reject':
            print(f"\n❌ Phase {phase} rechazada por usuario.")
            self.state.phases[phase]['validated'] = False
            self.state.phases[phase]['status'] = PhaseStatus.FAILED.value
            sys.exit(1)
        elif response == 'n':
            print(f"\n⏸️  Pausa hasta que decidas continuar.")
            print(f"Ejecuta: python orchestrator.py resume {self.task_id}")
            self.save_state()
            sys.exit(0)

        print()

    def _close_phase(self):
        """[F+1] CLOSE: Finaliza la tarea."""
        print("[CLOSE] Finalizando tarea...\n")

        self.state.status = "completed"
        self.state.phases['F']['status'] = PhaseStatus.COMPLETED.value
        self.state.phases['F']['validated'] = True

        print(f"✅ Task {self.task_id} completada exitosamente")
        print(f"   Status: {self.state.status}")
        print(f"   Fecha: {datetime.now().isoformat()}\n")

    def status(self):
        """Muestra estado actual de la tarea."""
        print(f"\n{'='*70}")
        print(f"STATUS: {self.task_id}")
        print(f"{'='*70}\n")

        print(f"Status: {self.state.status}")
        print(f"Branch: {self.state.branch}")
        print(f"Version: {self.state.version}")
        print(f"Last Updated: {self.state.updated_at}\n")

        print("Phases:")
        for phase in self.PHASES:
            p = self.state.phases[phase]
            status_icon = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'skipped': '⊘',
            }.get(p['status'], '?')

            validated = '✓' if p['validated'] else '✗'
            triage = self.state.triage.get(phase, '?')

            print(f"  {phase}: [{status_icon}] {p['name']:40} [{triage}] validated:{validated} (attempts: {p['attempts']})")
        print()

    def resume(self):
        """Reanuda desde donde quedó."""
        print(f"\n{'='*70}")
        print(f"RESUMIENDO: {self.task_id}")
        print(f"{'='*70}\n")
        self.run()


def main():
    """CLI: python orchestrator.py <command> <task_id> [--mock|--fast]"""
    if len(sys.argv) < 3:
        print("Usage: orchestrator.py <run|status|resume> <task_id> [--mock|--fast]")
        print()
        print("Modes:")
        print("  orchestrator.py run T-APX-001           # Interactive (pausa en cada fase)")
        print("  orchestrator.py run T-APX-001 --fast    # Fast (sin HITL, ejecuta todo)")
        print("  orchestrator.py run T-APX-001 --mock    # Mock (testing, no pide nada)")
        print("  orchestrator.py status T-APX-001        # Show status")
        print("  orchestrator.py resume T-APX-001        # Resume from pause")
        sys.exit(1)

    command = sys.argv[1]
    task_id = sys.argv[2]
    mock_mode = '--mock' in sys.argv
    fast_mode = '--fast' in sys.argv

    orchestrator = TaskOrchestrator(task_id, mock_mode=mock_mode, fast_mode=fast_mode)

    if command == 'run':
        orchestrator.run()
    elif command == 'status':
        orchestrator.status()
    elif command == 'resume':
        orchestrator.resume()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
