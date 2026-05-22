#!/usr/bin/env python3
"""
Orquestador del Bucle de Autocorrección (Self-Correction Loop) de Aprexx v3.0.
Este script automatiza la ejecución de tests y validaciones de calidad locales,
generando archivos de feedback estructurados para que los subagentes puedan
iterar sobre el código de forma autónoma sin intervención del usuario.
"""

import os
import sys
import argparse
import subprocess
import json
import re

SCRATCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scratch"))
FEEDBACK_FILE = os.path.join(SCRATCH_DIR, "qa_feedback.md")
STATUS_FILE = os.path.join(SCRATCH_DIR, "coder_status.json")

def write_status(phase, status, message):
    data = {
        "phase": phase,
        "status": status,
        "message": message
    }
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def run_step_command(cmd, cwd=None):
    """Ejecuta un comando de validación y captura su salida."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.returncode, result.stdout
    except Exception as e:
        return -1, f"Error al ejecutar el comando '{cmd}': {str(e)}"

def format_feedback(errors_by_step):
    """Genera el reporte de feedback en formato markdown para el subagente Coder."""
    markdown = []
    markdown.append("# 🔍 Reporte de Calidad y Feedback del Validador Autónomo\n")
    markdown.append("Se han detectado problemas que impiden completar la fase actual. Por favor, corrige los siguientes puntos:\n")
    
    for step_name, (code, output) in errors_by_step.items():
        markdown.append(f"## ❌ Fallo en: {step_name}")
        markdown.append(f"**Código de salida:** `{code}`")
        markdown.append("### Detalles de la salida:")
        markdown.append("```text")
        # Limitar la salida para no saturar la ventana de contexto
        lines = output.splitlines()
        if len(lines) > 50:
            output_snippet = "\n".join(lines[:25]) + "\n\n... [Salida recortada por brevedad] ...\n\n" + "\n".join(lines[-25:])
        else:
            output_snippet = output
        markdown.append(output_snippet)
        markdown.append("```\n")
        markdown.append("---")
        
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown))

def execute_red_phase(test_cmd, cwd):
    """Fase Roja: Verifica que los tests fallen inicialmente (TDD)."""
    print("🔴 Ejecutando Fase Roja (TDD - Validando que los tests fallen)...")
    write_status("red_phase", "running", "Ejecutando tests de la fase roja...")
    
    code, output = run_step_command(test_cmd, cwd)
    
    if code == 0:
        # Si el test pasa sin cambios, no estamos en fase roja real o falta escribir los nuevos escenarios
        msg = "Fallo en Fase Roja: Los tests han pasado con éxito. Para cumplir TDD, debes escribir primero escenarios/tests que fallen."
        print(f"❌ {msg}")
        format_feedback({"Fase Roja (TDD)": (code, output + f"\n\n👉 NOTA: {msg}")})
        write_status("red_phase", "failed", msg)
        return False
    else:
        print("✅ Los tests fallan como se esperaba. Fase Roja completada con éxito.")
        write_status("red_phase", "success", "Fase roja completada: los tests fallan correctamente.")
        if os.path.exists(FEEDBACK_FILE):
            os.remove(FEEDBACK_FILE)
        return True

def execute_green_qa_phase(test_cmd, cwd, lint_cmd=None, typecheck_cmd=None):
    """Fase Verde y QA: Verifica que los tests pasen, lints y types estén limpios."""
    print("🟢 Ejecutando Fase Verde y QA (Validando implementación y calidad)...")
    write_status("green_qa_phase", "running", "Ejecutando suite de pruebas y linters...")
    
    errors = {}
    
    # 1. Ejecutar Tests
    code, output = run_step_command(test_cmd, cwd)
    if code != 0:
        errors["Tests Unitarios / Integración"] = (code, output)
        print("❌ Los tests están fallando.")
        
    # 2. Ejecutar Linter si está definido
    if lint_cmd:
        code_lint, output_lint = run_step_command(lint_cmd, cwd)
        if code_lint != 0:
            errors["Linter / Estilo de Código"] = (code_lint, output_lint)
            print("❌ El linter ha encontrado errores.")
            
    # 3. Ejecutar Typecheck si está definido
    if typecheck_cmd:
        code_type, output_type = run_step_command(typecheck_cmd, cwd)
        if code_type != 0:
            errors["Type Checking"] = (code_type, output_type)
            print("❌ Fallo en la comprobación de tipos.")
            
    if errors:
        format_feedback(errors)
        write_status("green_qa_phase", "failed", "Se encontraron fallos de calidad o tests rotos. Revisa qa_feedback.md.")
        return False
    else:
        print("✅ Todos los checks han pasado con éxito. Código apto para producción.")
        write_status("green_qa_phase", "success", "Fase Verde/QA superada con éxito.")
        if os.path.exists(FEEDBACK_FILE):
            os.remove(FEEDBACK_FILE)
        return True

def main():
    parser = argparse.ArgumentParser(description="Orquestador de calidad para bucles de autocorrección multi-agente.")
    parser.add_argument("--phase", choices=["red", "green", "all"], required=True, help="Fase del ciclo a validar (red/green/all).")
    parser.add_argument("--test-cmd", required=True, help="Comando para ejecutar la suite de pruebas.")
    parser.add_argument("--cwd", default=".", help="Directorio de trabajo para ejecutar los comandos.")
    parser.add_argument("--lint-cmd", help="Comando opcional para correr el linter.")
    parser.add_argument("--typecheck-cmd", help="Comando opcional para correr el type checker.")
    
    args = parser.parse_args()
    
    cwd_abs = os.path.abspath(args.cwd)
    
    if args.phase == "red":
        success = execute_red_phase(args.test_cmd, cwd_abs)
    elif args.phase == "green":
        success = execute_green_qa_phase(args.test_cmd, cwd_abs, args.lint_cmd, args.typecheck_cmd)
    else: # all
        success = execute_red_phase(args.test_cmd, cwd_abs)
        if success:
            # Esperar a que el agente implemente para correr la fase verde
            print("Fase Roja superada. Interrupción controlada para codificación. Ejecuta con --phase green una vez implementado.")
            sys.exit(0)
            
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
