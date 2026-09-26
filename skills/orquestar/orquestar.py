#!/usr/bin/env python3
"""Bucle del orquestador: deduce la fase del disco y lanza un arnés por paso.

El estado se calcula siempre a partir de artefactos (documentos, frontmatter del
backlog, ramas git), nunca de lo que el modelo diga que ha hecho.

Salida: 0 = producto terminado, 2 = parada para el humano, 1 = error.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HARNESS = {
    'claude': ['claude', '-p', '{prompt}', '--dangerously-skip-permissions'],
    'codex': ['codex', 'exec', '--full-auto', '{prompt}'],
    'gemini': ['gemini', '--yolo', '-p', '{prompt}'],
    'cursor': ['cursor-agent', '-p', '--force', '{prompt}'],
}
SKILL = Path(__file__).resolve().parent / 'SKILL.md'
CERRADO = {'completed', 'cancelled'}
PROMPT = ('Lee {skill} y ejecuta en modo orquestado el paso "{paso}"{args}. '
          'No hagas preguntas: aplica las reglas del modo orquestado.')


def git(*args):
    r = subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8')
    return r.stdout.strip()


def frontmatter(path):
    m = re.match(r'---\s*\n(.*?)\n---', path.read_text(encoding='utf-8'), re.S)
    if not m:
        return {}
    pares = (l.split(':', 1) for l in m[1].splitlines() if ':' in l)
    return {k.strip(): v.strip().strip('"\'') for k, v in pares}


def backlog_dirs(root):
    base, tareas, bugs = 'docs/plan/', 'tasks/', 'bugs/'
    try:
        import yaml
        m = yaml.safe_load((root / 'task_config.yaml').read_text(encoding='utf-8'))['levels']['master']
        base, tareas, bugs = m['path'], m['folders']['tasks'], m['folders']['bugs']
    except Exception:
        pass
    return root / base / tareas, root / base / bugs


def backlog(root):
    """Tareas y bugs maestros con su estado, versión y peso."""
    out = []
    for tipo, d in zip(('task-dev', 'bug-fix'), backlog_dirs(root)):
        for f in sorted(d.glob('*.md')) if d.is_dir() else []:
            fm = frontmatter(f)
            if not fm.get('id') or fm.get('parent_id'):
                continue
            peso = fm.get('weight', '')
            out.append({'paso': tipo, 'id': fm['id'], 'status': fm.get('status', 'backlog'),
                        'version': fm.get('version', ''),
                        'weight': int(peso) if peso.lstrip('-').isdigit() else 0})
    return out


def vkey(v):
    m = re.match(r'v?(\d+)\.(\d+)', v or '')
    return (int(m[1]), int(m[2])) if m else None


def estado(root, docs):
    """Devuelve ('PASO', paso, arg, rama) | ('PARAR', motivo) | ('FIN', motivo)."""
    d = root / docs
    if not (root / 'task_config.yaml').exists():
        return ('PARAR', 'Falta task_config.yaml en la raíz del proyecto.')
    if not (d / 'requirements.md').exists():
        return ('PARAR', f'Falta la idea: escríbela en {docs}/requirements.md o usa --idea.')
    if not (d / 'req_analysis.md').exists():
        return ('PASO', 'ciclo-requisitos', '', None)
    if 'REQUIERE_ACLARACION' in (d / 'req_analysis.md').read_text(encoding='utf-8').splitlines()[0]:
        return ('PARAR', f'Requisitos con preguntas sin valor por defecto seguro: revisa {docs}/req_analysis.md.')
    for doc, paso in (('needs_analysis.md', 'needs-analysis'), ('platform_plan.md', 'platform-plan')):
        if not (d / doc).exists():
            return ('PASO', paso, '', None)
    items = backlog(root)
    if not (d / 'work_plan.md').exists() or not items:
        return ('PASO', 'work-plan', '', None)

    pendientes = [i for i in items if i['status'] not in CERRADO and vkey(i['version'])]
    abiertas = [b.lstrip('* ').strip() for b in git('branch', '--list', 'release/v*').splitlines()]
    for rama in sorted(abiertas, key=lambda b: vkey(b.split('/')[1]) or (0, 0)):
        v = rama.split('/')[1]
        suyas = [i for i in pendientes if vkey(i['version']) == vkey(v)]
        if not suyas:
            return ('PARAR', f'Versión {v} terminada. Revisa docs/review/versions/{v}-revision.md: '
                             f'registra defectos con /bug-add o cierra con /release, y relanza.')
        i = min(suyas, key=lambda i: (i['status'] != 'in_progress', i['weight']))
        return ('PASO', i['paso'], i['id'], rama)
    if not pendientes:
        return ('FIN', 'Todas las tareas con versión están cerradas.')
    v = min(vkey(i['version']) for i in pendientes)
    return ('PASO', 'start-version', f'v{v[0]}.{v[1]}', None)


def firma(root, docs):
    return (estado(root, docs), git('rev-parse', 'HEAD'), git('status', '--porcelain'),
            tuple((i['id'], i['status']) for i in backlog(root)))


def comando(a, prompt):
    plantilla = a.cmd.split() if a.cmd else HARNESS[a.harness]
    exe = shutil.which(plantilla[0])
    if not exe:
        sys.exit(f'No se encuentra el arnés "{plantilla[0]}" en el PATH.')
    return [exe] + [p.replace('{prompt}', prompt) for p in plantilla[1:]]


def main():
    ap = argparse.ArgumentParser(description='Orquestador: de la idea al producto, paso a paso.')
    ap.add_argument('--harness', choices=HARNESS, default='claude')
    ap.add_argument('--cmd', help='plantilla propia del arnés, con {prompt} (sustituye a --harness)')
    ap.add_argument('--docs', default='docs/requirements', help='carpeta de requisitos y planes')
    ap.add_argument('--test', help='comando de la suite; debe pasar al cerrar cada tarea')
    ap.add_argument('--idea', help='texto de la idea; crea <docs>/requirements.md si no existe')
    ap.add_argument('--max-pasos', type=int, default=100)
    ap.add_argument('--reintentos', type=int, default=2, help='pasos seguidos sin progreso antes de parar')
    ap.add_argument('--estado', action='store_true', help='muestra el estado y sale')
    a = ap.parse_args()
    root = Path.cwd()
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    if a.idea and not (root / a.docs / 'requirements.md').exists():
        (root / a.docs).mkdir(parents=True, exist_ok=True)
        (root / a.docs / 'requirements.md').write_text(a.idea + '\n', encoding='utf-8')

    skill = os.path.relpath(SKILL, root).replace('\\', '/')
    sin_progreso = 0
    for n in range(1, a.max_pasos + 1):
        e = estado(root, a.docs)
        print(f'\n[orquestar] {n}. {e[0]}: ' + ' '.join(str(x) for x in e[1:] if x), flush=True)
        if a.estado or e[0] != 'PASO':
            return 0 if e[0] in ('FIN', 'PASO') else 2
        _, paso, arg, rama = e
        if rama and git('branch', '--show-current') != rama:
            if git('status', '--porcelain'):
                print(f'[orquestar] PARAR: cambios sin commitear; no puedo cambiar a {rama}.')
                return 2
            git('checkout', '-q', rama)

        antes = firma(root, a.docs)
        cerradas = {i['id'] for i in backlog(root) if i['status'] in CERRADO}
        prompt = PROMPT.format(skill=skill, paso=paso, args=f' con "{arg}"' if arg else '')
        subprocess.run(comando(a, prompt), cwd=root)

        if a.test and any(i['status'] in CERRADO and i['id'] not in cerradas for i in backlog(root)):
            if subprocess.run(a.test, shell=True, cwd=root).returncode:
                print(f'[orquestar] PARAR: {arg} se ha cerrado pero la suite falla ({a.test}).')
                return 2
        if firma(root, a.docs) == antes:
            sin_progreso += 1
            print(f'[orquestar] sin progreso ({sin_progreso}/{a.reintentos})')
            if sin_progreso >= a.reintentos:
                print(f'[orquestar] PARAR: "{paso}" no avanza tras {a.reintentos} intentos.')
                return 2
        else:
            sin_progreso = 0
    print(f'[orquestar] PARAR: alcanzado --max-pasos={a.max_pasos}.')
    return 2


if __name__ == '__main__':
    sys.exit(main())
