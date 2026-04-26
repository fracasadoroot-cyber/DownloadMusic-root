#!/usr/bin/env python3
# Fracasadoroot
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _ensure_ffmpeg() -> None:
    if _which("ffmpeg") and _which("ffprobe"):
        return
    raise SystemExit(
        "No se encontró ffmpeg/ffprobe en PATH.\n"
        "- Linux (Debian/Ubuntu): sudo apt update && sudo apt install -y ffmpeg\n"
        "- Windows (winget): winget install Gyan.FFmpeg\n"
        "- Windows (choco): choco install ffmpeg\n"
    )


def _build_ydl_command(args: argparse.Namespace, url: str) -> list[str]:
    base_out_dir = Path(args.out).expanduser().resolve()
    out_dir = (base_out_dir / ("videos" if args.video else "audio")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Base command
    cmd: list[str] = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--newline",
        "--no-mtime",
        "--ignore-errors",
        "--force-overwrites" if args.overwrite else "--no-overwrites",
        "--paths",
        str(out_dir),
        "-o",
        args.template,
    ]

    if args.video:
        # Video: preferimos MP4 cuando sea posible.
        # - bestvideo*+bestaudio: mejor calidad (requiere merge con ffmpeg)
        # - fallback a "best" si no hay streams separados
        cmd += [
            "-f",
            "bestvideo*+bestaudio/best",
            "--merge-output-format",
            "mp4",
        ]
    else:
        audio_format = args.format
        if audio_format not in {"mp3", "m4a"}:
            raise SystemExit("--format debe ser mp3 o m4a")

        cmd += [
            "-f",
            "bestaudio/best",
            "--extract-audio",
            "--audio-format",
            audio_format,
        ]

        if args.quality:
            cmd += ["--audio-quality", args.quality]

    if args.embed_metadata:
        cmd += ["--embed-metadata"]

    if args.embed_thumbnail:
        cmd += ["--embed-thumbnail"]

    if args.add_metadata:
        cmd += ["--add-metadata"]

    if args.no_playlist:
        cmd += ["--no-playlist"]

    if args.cookies:
        cmd += ["--cookies", str(Path(args.cookies).expanduser())]

    if args.proxy:
        cmd += ["--proxy", args.proxy]

    if args.limit_rate:
        cmd += ["--limit-rate", args.limit_rate]

    if args.retries is not None:
        cmd += ["--retries", str(args.retries)]

    if args.fragment_retries is not None:
        cmd += ["--fragment-retries", str(args.fragment_retries)]

    if args.no_check_certificates:
        cmd += ["--no-check-certificates"]

    if args.verbose:
        cmd += ["-v"]

    cmd.append(url)
    return cmd


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ytmusic-dl",
        description="Descarga audio o video desde links (usa yt-dlp + ffmpeg).",
    )
    p.add_argument("url", nargs="*", help="Uno o más links (YouTube u otros soportados por yt-dlp).")
    p.add_argument(
        "-i",
        "--input-file",
        help="Archivo de texto con 1 URL por línea (líneas vacías o con # se ignoran).",
    )
    p.add_argument(
        "-o",
        "--out",
        default="downloads",
        help="Carpeta de salida (default: downloads).",
    )
    p.add_argument(
        "--format",
        default="mp3",
        choices=["mp3", "m4a"],
        help="Formato de audio (default: mp3). Ignorado si usas --video.",
    )
    p.add_argument(
        "--quality",
        default=None,
        help="Calidad para el convertidor (ej: 0, 5, 128K). Opcional. Ignorado si usas --video.",
    )
    p.add_argument(
        "--template",
        default="%(title)s [%(id)s].%(ext)s",
        help="Plantilla de nombre de archivo (default: \"%(title)s [%(id)s].%(ext)s\").",
    )
    kind = p.add_mutually_exclusive_group()
    kind.add_argument("--video", action="store_true", help="Descarga video (MP4 cuando sea posible).")
    kind.add_argument("--audio", action="store_true", help="Descarga audio (default).")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--mix",
        action="store_true",
        help="Descarga playlists/mixes completos cuando el link los incluya.",
    )
    mode.add_argument(
        "--single",
        action="store_true",
        help="Descarga solo el video del URL (default).",
    )
    # Compatibilidad: mantenemos el flag viejo.
    p.add_argument(
        "--no-playlist",
        action="store_true",
        help="(Alias de --single) Si el link es playlist/mix, baja solo el video.",
    )
    p.add_argument("--cookies", help="Ruta a cookies.txt (útil para contenido con login/age).")
    p.add_argument("--proxy", help="Proxy, ej: socks5://127.0.0.1:9050")
    p.add_argument("--limit-rate", help="Limita velocidad, ej: 1M, 500K")
    p.add_argument("--retries", type=int, default=None, help="Reintentos (yt-dlp --retries).")
    p.add_argument("--fragment-retries", type=int, default=None, help="Reintentos por fragmento.")
    p.add_argument("--no-check-certificates", action="store_true", help="Desactiva validación TLS (no recomendado).")
    ow = p.add_mutually_exclusive_group()
    ow.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescribe si el archivo ya existe.",
    )
    ow.add_argument(
        "--no-overwrite",
        action="store_true",
        help="No sobrescribas si el archivo ya existe (default).",
    )
    p.add_argument("--add-metadata", action="store_true", help="Escribe metadata básica (yt-dlp).")
    p.add_argument("--embed-metadata", action="store_true", help="Incrusta metadata (requiere ffmpeg).")
    p.add_argument("--embed-thumbnail", action="store_true", help="Incrusta thumbnail (requiere ffmpeg).")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose (yt-dlp -v).")
    p.set_defaults(no_playlist=True)
    p.set_defaults(overwrite=False)
    args = p.parse_args(argv)

    # Política:
    # - default: single (no-playlist)
    # - --mix: permite playlist/mix
    # - --single o --no-playlist: fuerza single
    if getattr(args, "mix", False):
        args.no_playlist = False
    elif getattr(args, "single", False) or getattr(args, "no_playlist", False):
        args.no_playlist = True

    # Default: NO sobrescribir
    if getattr(args, "no_overwrite", False):
        args.overwrite = False

    # Default: audio (si no escogió nada)
    if getattr(args, "audio", False):
        args.video = False

    return args


def _read_urls_from_file(path: str) -> list[str]:
    p = Path(path).expanduser()
    if not p.exists():
        raise SystemExit(f"No existe el archivo: {p}")
    urls: list[str] = []
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        urls.append(s)
    return urls


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    urls: list[str] = []
    if args.input_file:
        urls.extend(_read_urls_from_file(args.input_file))
    if args.url:
        urls.extend(args.url)

    if not urls:
        print("No diste URLs. Ejemplo: ytmusic-dl https://youtu.be/XXXX", file=sys.stderr)
        return 2

    _ensure_ffmpeg()

    failures = 0
    for url in urls:
        cmd = _build_ydl_command(args, url)
        print("\n$ " + " ".join(_quote_arg(a) for a in cmd))
        r = subprocess.run(cmd, env=_sanitized_env(), check=False)
        if r.returncode != 0:
            failures += 1

    return 1 if failures else 0


def _sanitized_env() -> dict[str, str]:
    env = dict(os.environ)
    # Evita que yt-dlp herede settings raros de python en algunos setups.
    env.pop("PYTHONPATH", None)
    return env


def _quote_arg(s: str) -> str:
    if any(c in s for c in (" ", "\t", '"')):
        return '"' + s.replace('"', '\\"') + '"'
    return s


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

