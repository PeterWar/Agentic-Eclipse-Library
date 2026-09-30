#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

try_python() {
    candidate=$1
    shift
    if [ -x "$candidate" ] && "$candidate" -c 'import numpy, scipy, rawpy' >/dev/null 2>&1; then
        PYTHONDONTWRITEBYTECODE=1 exec "$candidate" "$script_dir/preflight.py" "$@"
    fi
}

if [ -n "${VIRTUAL_ENV:-}" ]; then
    try_python "$VIRTUAL_ENV/bin/python" "$@"
fi

path_python=$(command -v python3 2>/dev/null || true)
if [ -n "$path_python" ]; then
    try_python "$path_python" "$@"
fi

for candidate in "$HOME"/.venvs/*/bin/python "$HOME"/Downloads/*venv*/bin/python; do
    [ -e "$candidate" ] || continue
    try_python "$candidate" "$@"
done

printf '%s\n' "ERROR: no s'ha trobat cap Python amb numpy, scipy i rawpy." >&2
exit 127
