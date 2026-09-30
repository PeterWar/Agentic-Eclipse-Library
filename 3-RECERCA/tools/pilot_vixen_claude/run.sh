#!/bin/sh
# Detecta un Python que tingui el que cal. ⛔ Cap intèrpret escrit a pèl:
# el 26-07-2026 una actualització de Homebrew va deixar morts tots els .venv
# que n'anomenaven un.
set -eu
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

prova() {
    cand=$1
    shift
    [ -x "$cand" ] || return 1
    "$cand" -c 'import numpy, scipy, rawpy, cv2, tifffile' >/dev/null 2>&1 || return 1
    PYTHONDONTWRITEBYTECODE=1 exec "$cand" "$dir/pilot.py" "$@"
}

if [ -n "${VIRTUAL_ENV:-}" ]; then
    prova "$VIRTUAL_ENV/bin/python" "$@" || true
fi
for c in "$HOME"/Downloads/*venv*/bin/python "$HOME"/.venvs/*/bin/python \
         "$(command -v python3 2>/dev/null || echo /nonexistent)"; do
    [ -e "$c" ] || continue
    prova "$c" "$@" || true
done
echo "ERROR: cap Python amb numpy, scipy, rawpy, cv2 i tifffile." >&2
echo "       Prova: ~/Downloads/eclipse_venv/bin/pip install <el que falti>" >&2
exit 127
