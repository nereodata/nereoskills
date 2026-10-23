"""Punto de entrada de línea de comandos para adevv."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from adevv import __version__, migrate, processes, updater
from adevv.store import (
    get_active_info,
    get_active_version_dir,
    get_adevv_home,
    get_config,
    get_sync_registry,
    get_update_state,
    set_config,
    set_update_state,
)
from adevv.sync import (
    DESTINOS,
    EstadoDestino,
    planificar_sincronizacion,
    sincronizar_destinos,
)


def comando_actualizar(target_version: Optional[str], out: TextIO, err: TextIO) -> int:
    """Ejecuta la orden adevv actualizar [target_version]."""
    act = get_active_info()
    version_actual = act.get("version", __version__) if act else __version__

    if target_version is None:
        state = get_update_state()
        state.pop("fallida", None)
        set_update_state(state)

        config = get_config()
        if not config.get("auto_update", True):
            config["auto_update"] = True
            set_config(config)
            print("Actualización automática reactivada.", file=out)

        res, msg, ver = updater.evaluar_comprobacion_actualizacion(forzada=True)
        if res == updater.ResultadoActualizacion.APLICADA:
            if msg:
                print(msg, file=out)
            return 0
        elif res == updater.ResultadoActualizacion.AL_DIA:
            if msg:
                print(msg, file=out)
            return 0
        elif res == updater.ResultadoActualizacion.APLAZADA:
            if msg:
                print(msg, file=err)
            return 1
        elif res in (updater.ResultadoActualizacion.FALLIDA, updater.ResultadoActualizacion.SIN_RED):
            if msg:
                print(msg, file=err)
            return 1
        else:
            if msg:
                print(msg, file=out)
            return 0

    versiones, mapa_commits, err_q = updater.consultar_versiones_publicadas()
    if err_q:
        remote = os.environ.get("ADEVV_ORIGIN_URL") or "https://github.com/nereodata/nereoskills.git"
        print(f"No se pudo consultar {remote}: {err_q}. Sigues con la {version_actual}.", file=err)
        return 1

    if target_version not in versiones:
        top5 = list(reversed(versiones))[:5]
        print(f"{target_version} no es una versión publicada. Publicadas: {', '.join(top5)}.", file=err)
        return 1

    if target_version == version_actual:
        print(f"Adevv {target_version} ya está instalado.", file=out)
        return 0

    bucles = processes.hay_bucles_en_marcha()
    if bucles:
        lista_bucles = ", ".join(processes.formatear_proceso_ui(b) for b in bucles)
        print(f"No se puede instalar {target_version} con bucles en marcha: {lista_bucles}.", file=err)
        return 1

    commit_hash = mapa_commits.get(target_version)
    state = get_update_state()
    state.pop("aplazada", None)
    set_update_state(state)
    ok, causa, desfasados = updater.instalar_version_publicada(target_version=target_version, commit_hash=commit_hash)
    if not ok:
        print(f"No se pudo instalar {target_version}: {causa}.", file=err)
        return 1

    mayor_publicada = versiones[-1]
    if updater._version_es_mayor(mayor_publicada, target_version):
        cfg = get_config()
        cfg["auto_update"] = False
        set_config(cfg)
        print(f"Actualización automática desactivada; `adevv actualizar` la reactiva.", file=out)
    else:
        print(f"Adevv {target_version} instalado con éxito.", file=out)

    return 0


def _resincronizar_desfasados_al_arrancar(out: TextIO, err: TextIO) -> None:
    """Resincroniza destinos desfasados si no hay bucles en marcha, o avisa en 24h."""
    if os.environ.get("ORQUESTAR_PASO"):
        return

    act = get_active_info()
    version_activa = act.get("version", __version__) if act else __version__
    origen_dir = get_active_version_dir()

    bucles_vivos = processes.hay_bucles_en_marcha()

    desfasados = []
    for target_key in DESTINOS.keys():
        plan = planificar_sincronizacion(target_key, origen_dir, version_activa)
        if plan["estado"] == EstadoDestino.DESFASADO:
            registro = get_sync_registry(target_key)
            v_reg = (registro.get("version") if registro else None) or "anterior"
            desfasados.append((target_key, plan["nombre"], v_reg))

    if not desfasados:
        return

    if bucles_vivos:
        lista_bucles = ", ".join(processes.formatear_proceso_ui(b) for b in bucles_vivos)
        for _, nombre, v_reg in desfasados:
            msg = f"{nombre} sigue con la {v_reg}; se sincronizará cuando no haya bucles en marcha: {lista_bucles}."
            print(msg, file=err)
    else:
        sincronizar_destinos(origen_dir=origen_dir, version=version_activa)
        for _, nombre, _ in desfasados:
            msg = f"{nombre} sincronizado con la {version_activa}."
            print(msg, file=err)


def _describir_escritos_destino(destino_key: str, origen_dir: Path) -> str:
    """Genera la descripción del contenido escrito en un destino (ej. 24 skills, 5 agentes)."""
    skills_dir = origen_dir / "skills"
    agents_dir = origen_dir / "agents"
    workflows_dir = origen_dir / "workflows"

    num_skills = 0
    if skills_dir.exists() and skills_dir.is_dir():
        num_skills = sum(1 for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith("."))

    if destino_key in ("claude", "codex"):
        num_agentes = 0
        if destino_key == "claude" and agents_dir.exists():
            num_agentes = sum(1 for f in agents_dir.iterdir() if f.is_file() and f.suffix == ".md")
        elif destino_key == "codex" and (agents_dir / "codex").exists():
            num_agentes = sum(1 for f in (agents_dir / "codex").iterdir() if f.is_file() and f.suffix == ".toml")

        partes = []
        if num_skills > 0:
            partes.append(f"{num_skills} skills")
        if num_agentes > 0:
            partes.append(f"{num_agentes} agentes")
        return ", ".join(partes) or "sin contenido"

    elif destino_key == "agy":
        num_wf = 0
        if workflows_dir.exists():
            num_wf = sum(1 for f in workflows_dir.iterdir() if f.is_file() and f.suffix == ".md")

        partes = []
        if num_skills > 0:
            partes.append(f"{num_skills} skills")
        if num_wf > 0:
            partes.append(f"{num_wf} workflows")
        return ", ".join(partes) or "sin contenido"

    return "sincronizado"


def comando_instalar(forzar: bool, out: TextIO, err: TextIO) -> int:
    """Ejecuta la orden adevv instalar [--forzar]."""
    act = get_active_info()
    version = act.get("version", __version__) if act else __version__
    origen = act.get("origen", "publicada") if act else "publicada"
    versions_dir = get_adevv_home() / "versions" / version

    if origen != "desarrollo" and (not act or not versions_dir.exists() or (forzar and not act.get("commit"))):
        version = __version__
        updater.materializar_version_local(version)
        updater.limpiar_versiones_antiguas()

    origen_dir = get_active_version_dir()
    resultados = sincronizar_destinos(origen_dir=origen_dir, version=version, forzar=forzar)

    for destino_key, res in resultados.items():
        nombre = res["nombre"]
        estado = res["estado"]
        detalle = res.get("detalle")
        sin_cambios = res.get("sin_cambios", False)
        conflictos = res.get("conflictos", [])

        if estado == EstadoDestino.NO_DETECTADO:
            print(f"{nombre}: {detalle or 'no detectado'}", file=out)
        elif estado == EstadoDestino.DESACTIVADO:
            print(f"{nombre}: desactivado", file=out)
        elif sin_cambios:
            print(f"{nombre}: sin cambios", file=out)
        elif estado == EstadoDestino.INCOMPLETO:
            desc = _describir_escritos_destino(destino_key, origen_dir)
            print(f"{nombre}: {desc} ({len(conflictos)} conflictos)", file=out)
            for c in conflictos[:20]:
                print(f"  conflicto: {c}", file=out)
            if len(conflictos) > 20:
                print(f"  ... y {len(conflictos) - 20} más (total {len(conflictos)})", file=out)
        else:
            desc = _describir_escritos_destino(destino_key, origen_dir)
            print(f"{nombre}: {desc}", file=out)

    return 0


def comando_version(out: TextIO) -> int:
    """Muestra la versión de Adevv, estado de cada arnés y metadatos de actualización."""
    act = get_active_info()
    version = act.get("version", __version__) if act else __version__
    origen = act.get("origen", "publicada") if act else "publicada"

    if origen == "desarrollo":
        print(f"Adevv {version} (desarrollo)", file=out)
    else:
        print(f"Adevv {version}", file=out)

    for target_key in DESTINOS.keys():
        cfg = DESTINOS[target_key]
        nombre = cfg.get("nombre", target_key)
        plan = planificar_sincronizacion(target_key, get_active_version_dir(), version)
        estado = plan["estado"]
        detalle = plan.get("detalle")
        conflictos = plan.get("conflictos", [])

        registro = get_sync_registry(target_key)
        version_reg = (registro.get("version") if registro else None) or version

        if estado == EstadoDestino.NO_DETECTADO:
            print(f"{nombre}: {detalle or 'no detectado'}", file=out)
        elif estado == EstadoDestino.DESACTIVADO:
            print(f"{nombre}: desactivado", file=out)
        elif estado == EstadoDestino.DESFASADO:
            print(f"{nombre} {version_reg} (pendiente de sincronizar)", file=out)
        elif estado == EstadoDestino.INCOMPLETO:
            print(f"{nombre} {version_reg} ({len(conflictos)} conflictos)", file=out)
        else:
            print(f"{nombre} {version_reg}", file=out)

    config = get_config()
    auto_update = "sí" if config.get("auto_update", True) else "no"
    print(f"actualización automática: {auto_update}", file=out)

    update_state = get_update_state()
    last_check_at = update_state.get("last_checked_at")
    last_check_status = update_state.get("last_checked_status")
    if last_check_at and last_check_status:
        status_map = {
            "AL_DIA": "al día",
            "APLICADA": "aplicada",
            "APLAZADA": "aplazada",
            "FALLIDA": "fallida",
            "SIN_RED": "sin red",
        }
        status_str = status_map.get(last_check_status, str(last_check_status).lower())
        print(f"última comprobación: {last_check_at} ({status_str})", file=out)

    last_applied_at = update_state.get("last_applied_at")
    last_applied_ver = update_state.get("last_applied_version")
    if last_applied_at and last_applied_ver:
        print(f"actualizado a {last_applied_ver} {last_applied_at}", file=out)

    return 0


def _resolver_script(rel_path: str) -> Path:
    """Resuelve la ruta de un script en la versión instalada o en el paquete fuente."""
    candidate = get_active_version_dir() / rel_path
    if candidate.exists():
        return candidate
    repo_fallback = Path(__file__).resolve().parents[1] / rel_path
    if repo_fallback.exists():
        return repo_fallback
    return candidate


def _despachar_script(script_path: Path, script_args: List[str], out: TextIO, err: TextIO) -> int:
    """Ejecuta un script de Python respetando los streams de salida proporcionados."""
    if not script_path.exists():
        print(f"Error: no se encuentra el script {script_path}", file=err)
        return 1

    if out is sys.stdout and err is sys.stderr:
        proc = subprocess.run([sys.executable, str(script_path), *script_args])
        return proc.returncode
    else:
        proc = subprocess.run(
            [sys.executable, str(script_path), *script_args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if proc.stdout:
            out.write(proc.stdout)
        if proc.stderr:
            err.write(proc.stderr)
        return proc.returncode


def main_cli(args: Optional[List[str]] = None, out: Optional[TextIO] = None, err: Optional[TextIO] = None) -> int:
    """Punto de entrada de adevv."""
    out_stream = out if out is not None else sys.stdout
    err_stream = err if err is not None else sys.stderr

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="adevv", description="Adevv: herramientas globales para agentes de IA")
    parser.add_argument("-v", "--version", action="store_true", help="muestra la versión y el estado de los arneses")

    subparsers = parser.add_subparsers(dest="subcommand")
    instalar_parser = subparsers.add_parser("instalar", help="sincroniza las carpetas de los arneses")
    instalar_parser.add_argument("--forzar", action="store_true", help="sobrescribe archivos del registro editados a mano")
    actualizar_parser = subparsers.add_parser("actualizar", help="actualiza adevv a la última versión publicada o a una específica")
    actualizar_parser.add_argument("target_version", nargs="?", default=None, help="versión específica X.Y.Z a instalar")
    subparsers.add_parser("orquestar", add_help=False, help="despacha el bucle o comandos de orquestación")
    subparsers.add_parser("metrics", add_help=False, help="muestra métricas de consumo y exporta CSV")
    subparsers.add_parser("metricas", add_help=False, help="muestra métricas de consumo y exporta CSV")
    subparsers.add_parser("telegram", add_help=False, help="despacha el gateway de Telegram")
    subparsers.add_parser("release", add_help=False, help="despacha scripts de gestión de lanzamientos")
    subparsers.add_parser("migrar", help="diagnostica la migración de submódulo .agents a adevv")

    if args and args[0] in ("metrics", "metricas"):
        raw_sub = args[1:]
        norm_sub = [
            "--version-filtro" if tok in ("--version", "-v") else (
                f"--version-filtro={tok.split('=', 1)[1]}" if tok.startswith("--version=") else tok
            )
            for tok in raw_sub
        ]
        res, msg, ver = updater.evaluar_comprobacion_actualizacion(es_instalar=False)
        if msg:
            print(msg, file=err_stream)
        _resincronizar_desfasados_al_arrancar(out_stream, err_stream)
        script_path = _resolver_script("skills/orquestar/orquestar.py")
        return _despachar_script(script_path, ["--metricas", *norm_sub], out_stream, err_stream)

    parsed, remaining = parser.parse_known_args(args)

    if parsed.subcommand is not None and parsed.subcommand != "actualizar":
        es_instalar = (parsed.subcommand == "instalar")
        res, msg, ver = updater.evaluar_comprobacion_actualizacion(es_instalar=es_instalar)
        if msg:
            print(msg, file=err_stream)

    _resincronizar_desfasados_al_arrancar(out_stream, err_stream)

    if parsed.version:
        return comando_version(out_stream)

    if parsed.subcommand == "actualizar":
        return comando_actualizar(parsed.target_version, out_stream, err_stream)

    if parsed.subcommand == "instalar":
        return comando_instalar(parsed.forzar, out_stream, err_stream)

    if parsed.subcommand == "migrar":
        return migrate.ejecutar_migrar(Path.cwd(), out_stream, err_stream)

    if parsed.subcommand == "orquestar":
        idx = args.index("orquestar")
        sub_args = args[idx + 1:]
        script_path = _resolver_script("skills/orquestar/orquestar.py")
        return _despachar_script(script_path, sub_args, out_stream, err_stream)

    if parsed.subcommand == "telegram":
        idx = args.index("telegram")
        sub_args = args[idx + 1:]
        script_path = _resolver_script("skills/telegram_gateway/gateway.py")
        return _despachar_script(script_path, sub_args, out_stream, err_stream)

    if parsed.subcommand == "release":
        idx = args.index("release")
        sub_args = args[idx + 1:]
        if not sub_args:
            print("Uso: adevv release manifiestos|completitud|changelog [argumentos...]", file=err_stream)
            return 1
        sub = sub_args[0]
        scripts_map = {
            "manifiestos": "skills/release/scripts/check_manifests_versions.py",
            "completitud": "skills/release/scripts/check_release_completeness.py",
            "changelog": "skills/release/scripts/generate_changelog_section.py",
        }
        if sub in scripts_map:
            script_path = _resolver_script(scripts_map[sub])
            return _despachar_script(script_path, sub_args[1:], out_stream, err_stream)
        else:
            print(f"Subcomando de release no reconocido: '{sub}'. Opciones: manifiestos, completitud, changelog", file=err_stream)
            return 1

    if not parsed.subcommand:
        return comando_version(out_stream)

    return 0


def main() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
