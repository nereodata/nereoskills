#!/usr/bin/env python3
"""
TaskOrchestrator: Ejecuta task-dev de forma determinista.

Obliga:
- Orden de fases (A → B → C → D → E → F)
- Validación de cada fase (no avanza sin validar)
- Persistencia de estado (recuperable si se interrumpe)
- HITL explícito (pausas donde Iván decide continuar)
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


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
    result: Optional[Dict[str, Any]] = None
    validated: bool = False
    validation_notes: str = ""
    error: Optional[str] = None
    attempts: int = 0


@dataclass
class TaskState:
    """Estado persistido de la tarea."""
    task_id: str
    version: str
    branch: str
    status: str                        # initialized | in_progress | completed | failed
    created_at: str
    updated_at: str
    triaged: bool = False
    triage: Dict[str, str] = None      # {A: EXEC, B: SKIP, ...}
    phases: Dict[str, Dict[str, Any]] = None
    last_phase_completed: Optional[str] = None
    next_phase_waiting: Optional[str] = None


class TaskOrchestrator:
    """Orquestador determinista de tareas."""

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

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.state_file = self.STATE_DIR / f'{task_id}.json'
        self.state = self._load_or_create_state()

    def _load_or_create_state(self) -> TaskState:
        """Carga estado existente o crea uno nuevo."""
        self.STATE_DIR.mkdir(exist_ok=True)

        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                return TaskState(**data)

        # Nuevo: necesita init
        return TaskState(
            task_id=self.task_id,
            version="",
            branch="",
            status="pending",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            phases={
                phase: asdict(PhaseState(
                    name=self.PHASE_NAMES[phase],
                    status=PhaseStatus.PENDING.value
                ))
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
        print(f"\n{'='*60}")
        print(f"TASK ORCHESTRATOR: {self.task_id}")
        print(f"{'='*60}\n")

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

                if not self._validate_phase(phase):
                    # Si validación falla, re-intenta o rechaza
                    self._handle_validation_failure(phase)
                    self.save_state()
                else:
                    # Validación ok, pausa HITL
                    self._hitl_pause(phase)
                    self.save_state()

        # [9] CLOSE
        self._close_phase()
        self.save_state()

    def _init_phase(self):
        """[1] INIT: Valida rama, carga metadatos."""
        print("[1] INIT: Validando configuración...\n")

        # TODO: Lógica real de init
        # - Validar rama (release/vX.Y o hotfix/vX.Y.Z)
        # - Cargar task.md
        # - Detectar versión

        self.state.status = "in_progress"
        self.state.branch = "release/v2.1"  # Mock
        self.state.version = "v2.1"

        print("✅ Rama: release/v2.1")
        print("✅ Versión: v2.1")
        print("✅ Task cargada\n")

    def _triage_phase(self):
        """[2] TRIAGE: Decide [EXEC]/[SKIP] para cada fase."""
        print("[2] TRIAGE: Analizando cambios...\n")

        # TODO: Lógica real de triaje
        # - Analizar qué cambios hay
        # - Decidir si se necesita cada fase

        self.state.triage = {
            'A': 'EXEC',  # BDD siempre (si hay nuevos reqs)
            'B': 'EXEC',  # Diseño (cambio estructurado)
            'C': 'EXEC',  # Tests (cambio de lógica)
            'D': 'EXEC',  # QA (siempre)
            'E': 'EXEC',  # Docs (si hay cambios)
            'F': 'EXEC',  # Commit (siempre)
        }

        print("Decisiones de triaje:")
        for phase, decision in self.state.triage.items():
            print(f"  Phase {phase} ({self.PHASE_NAMES[phase]}): [{decision}]")
        print()

        self.state.triaged = True

    def _should_execute(self, phase: str) -> bool:
        """¿Se debe ejecutar esta fase?"""
        return self.state.triage.get(phase) == 'EXEC' and \
               self.state.phases[phase]['status'] == PhaseStatus.PENDING.value

    def _execute_phase(self, phase: str):
        """Ejecuta una fase (llama a skill correspondiente)."""
        phase_state = self.state.phases[phase]
        skill_name = self._phase_to_skill(phase)

        print(f"[{phase}] {phase_state['name']}")
        print(f"    Ejecutando: {skill_name}\n")

        # TODO: Lógica real
        # - Generar prompt para la skill
        # - Llamar Claude API (o in-line si estamos en hilo)
        # - Capturar resultado
        # - Guardar en phase_state['result']

        phase_state['status'] = PhaseStatus.RUNNING.value
        phase_state['attempts'] += 1

        # Mock result
        phase_state['result'] = {
            'skill': skill_name,
            'output': f'Mock output de {skill_name}',
        }

        phase_state['status'] = PhaseStatus.COMPLETED.value

    def _phase_to_skill(self, phase: str) -> str:
        """Mapea fase a skill/skills a ejecutar."""
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

        print(f"    Validando Phase {phase}...")

        # TODO: Lógica real de validación
        # - Según la fase, validar que el resultado es válido
        # - review-spec: ¿retornó APROBADO?
        # - review-code: ¿retornó APROBADO?
        # - etc.

        # Mock: siempre válido
        phase_state['validated'] = True
        phase_state['validation_notes'] = "Mock validation passed"

        print(f"    ✅ Validación ok\n")
        return True

    def _handle_validation_failure(self, phase: str):
        """Maneja validación fallida (re-intenta o rechaza)."""
        phase_state = self.state.phases[phase]
        print(f"    ❌ Validación fallida (intento {phase_state['attempts']}/3)")
        # TODO: Lógica de reintento

    def _hitl_pause(self, phase: str):
        """Pausa en HITL para que Iván continúe o rechace."""
        self.state.last_phase_completed = phase

        next_phase_idx = self.PHASES.index(phase) + 1
        if next_phase_idx < len(self.PHASES):
            self.state.next_phase_waiting = self.PHASES[next_phase_idx]

        print(f"\n{'='*60}")
        print("HITL PAUSE")
        print(f"{'='*60}")
        print(f"Phase {phase} ({self.PHASE_NAMES[phase]}) completada y validada.\n")

        if self.state.next_phase_waiting:
            next_phase = self.state.next_phase_waiting
            print(f"Siguiente: Phase {next_phase} ({self.PHASE_NAMES[next_phase]})\n")
        else:
            print("Siguiente: CIERRE\n")

        # En Claude Code, esto se ve como mensajes normales.
        # El usuario responde en el chat, y si dice "continuar" (o similar),
        # se vuelve a invocar el orchestrador con resume().

        print("Continuar? (responde 'y' para continuar, 'n' para rechazar esta fase)")
        print(f"{'='*60}\n")

    def _close_phase(self):
        """[F+1] CLOSE: Finaliza la tarea."""
        print("[CLOSE] Cerrando tarea...\n")

        # TODO: Lógica real
        # - Ejecutar commit final
        # - Cerrar task.md (status: completed)

        self.state.status = "completed"
        self.state.phases['F']['status'] = PhaseStatus.COMPLETED.value
        self.state.phases['F']['validated'] = True

        print(f"✅ Task {self.task_id} completada")
        print(f"   Status: {self.state.status}")
        print(f"   Fecha: {datetime.now().isoformat()}\n")

    def status(self):
        """Muestra estado actual de la tarea."""
        print(f"\n{'='*60}")
        print(f"STATUS: {self.task_id}")
        print(f"{'='*60}\n")

        print(f"Status: {self.state.status}")
        print(f"Branch: {self.state.branch}")
        print(f"Version: {self.state.version}\n")

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

            print(f"  {phase}: [{status_icon}] {p['name']:40} [{triage}] validated:{validated}")
        print()

    def resume(self):
        """Reanuda desde donde quedó."""
        print(f"\nReanudando task {self.task_id}...\n")
        self.run()


def main():
    """CLI: python orchestrator.py <command> <task_id>"""
    if len(sys.argv) < 3:
        print("Usage: orchestrator.py <run|status|resume> <task_id>")
        sys.exit(1)

    command = sys.argv[1]
    task_id = sys.argv[2]

    orchestrator = TaskOrchestrator(task_id)

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
