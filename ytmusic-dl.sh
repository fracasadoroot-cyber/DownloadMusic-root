#!/usr/bin/env bash
# Fracasadoroot
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$here/.venv/bin/python" ]]; then
  echo "No hay .venv. Crea el entorno e instala dependencias:" 1>&2
  echo "  python3 -m venv .venv" 1>&2
  echo "  source .venv/bin/activate" 1>&2
  echo "  pip install -r requirements.txt" 1>&2
  exit 2
fi

"$here/.venv/bin/python" "$here/ytmusic_dl.py" "$@"

