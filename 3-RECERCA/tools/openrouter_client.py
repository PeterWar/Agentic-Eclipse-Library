#!/usr/bin/env python3
"""Client mínim d'OpenRouter per a la recerca de l'Eclipse 2026.

El secret es llegeix del Clauer de macOS i no s'emmagatzema al projecte.
La biblioteca estàndard és suficient; el controlador de captura no importa
ni depèn d'aquest mòdul.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable
import urllib.error
import urllib.request


API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/auto"
DEFAULT_KEYCHAIN_NAME = "OPENROUTER_API_KEY"
MAX_CONTEXT_BYTES = 2 * 1024 * 1024


class OpenRouterError(RuntimeError):
    """Error segur per mostrar a la línia d'ordres."""


def _keychain_commands(service: str | None = None) -> Iterable[list[str]]:
    security = "/usr/bin/security"
    if service:
        yield [security, "find-generic-password", "-w", "-s", service]
        yield [security, "find-generic-password", "-w", "-l", service]
        return

    yield [
        security,
        "find-generic-password",
        "-w",
        "-s",
        DEFAULT_KEYCHAIN_NAME,
    ]
    yield [
        security,
        "find-generic-password",
        "-w",
        "-l",
        DEFAULT_KEYCHAIN_NAME,
    ]
    yield [security, "find-generic-password", "-w", "-s", "openrouter.ai"]
    yield [security, "find-internet-password", "-w", "-s", "openrouter.ai"]


def load_api_key(service: str | None = None) -> str:
    """Carrega la clau de l'entorn o del Clauer, sense registrar-la."""

    environment_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if environment_key:
        return environment_key

    requested_service = service or os.environ.get(
        "OPENROUTER_KEYCHAIN_SERVICE"
    )
    for command in _keychain_commands(requested_service):
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        secret = result.stdout.strip()
        if result.returncode == 0 and secret:
            return secret

    raise OpenRouterError(
        "No s'ha pogut llegir la clau del Clauer. Desa-la com a "
        f"contrasenya genèrica del clauer «login», amb servei "
        f"{DEFAULT_KEYCHAIN_NAME}."
    )


def _safe_api_error(error: urllib.error.HTTPError) -> str:
    message = ""
    try:
        raw = error.read(64 * 1024).decode("utf-8", errors="replace")
        payload = json.loads(raw)
        api_error = payload.get("error", {})
        if isinstance(api_error, dict):
            message = str(api_error.get("message", "")).strip()
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass

    suffix = f": {message}" if message else ""
    return f"OpenRouter ha respost HTTP {error.code}{suffix}"


def api_request(
    method: str,
    path: str,
    *,
    api_key: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """Executa una petició JSON sense exposar cap capçalera sensible."""

    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "Eclipse-2026-research/1.0",
        "X-Title": "Eclipse 2026 research",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise OpenRouterError(_safe_api_error(error)) from None
    except urllib.error.URLError as error:
        reason = str(error.reason) if error.reason else "error de xarxa"
        raise OpenRouterError(
            f"No s'ha pogut contactar amb OpenRouter: {reason}"
        ) from None
    except (UnicodeError, json.JSONDecodeError):
        raise OpenRouterError(
            "OpenRouter ha retornat una resposta que no és JSON vàlid."
        ) from None


def check_connection(api_key: str) -> dict[str, Any]:
    response = api_request("GET", "/key", api_key=api_key, timeout=30)
    data = response.get("data")
    if not isinstance(data, dict):
        raise OpenRouterError("La resposta de verificació no té el format esperat.")
    return data


def _format_optional_amount(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return "no indicat"


def print_connection_summary(data: dict[str, Any]) -> None:
    tier = "gratuït" if data.get("is_free_tier") else "amb crèdit"
    print("OpenRouter: connexió correcta")
    print(f"Tipus de compte: {tier}")
    print(f"Ús acumulat: {_format_optional_amount(data.get('usage'))} USD")
    if data.get("limit") is not None:
        print(f"Límit: {_format_optional_amount(data.get('limit'))} USD")
    if data.get("limit_remaining") is not None:
        print(
            "Límit restant: "
            f"{_format_optional_amount(data.get('limit_remaining'))} USD"
        )
    if data.get("expires_at"):
        print(f"Caducitat de la clau: {data['expires_at']}")


def _read_text_file(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError as error:
        raise OpenRouterError(f"No es pot llegir {path}: {error}") from None
    if size > MAX_CONTEXT_BYTES:
        raise OpenRouterError(
            f"{path} supera el límit local de {MAX_CONTEXT_BYTES} bytes."
        )
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise OpenRouterError(
            f"{path} no és un fitxer de text UTF-8 llegible: {error}"
        ) from None


def build_user_prompt(
    prompt: str | None,
    prompt_file: Path | None,
    context_files: list[Path],
) -> str:
    if prompt is not None and prompt_file is not None:
        raise OpenRouterError(
            "Fes servir un text de prompt o --prompt-file, però no tots dos."
        )

    if prompt_file is not None:
        main_prompt = _read_text_file(prompt_file)
    elif prompt is not None:
        main_prompt = prompt
    elif not sys.stdin.isatty():
        main_prompt = sys.stdin.read()
    else:
        raise OpenRouterError(
            "Falta el prompt: passa'l com a argument, amb --prompt-file o per stdin."
        )

    if not main_prompt.strip():
        raise OpenRouterError("El prompt és buit.")

    sections = [main_prompt.strip()]
    for path in context_files:
        content = _read_text_file(path)
        sections.append(f"--- CONTEXT: {path} ---\n{content}")
    return "\n\n".join(sections)


def ask(
    *,
    api_key: str,
    model: str,
    prompt: str,
    system: str | None,
    max_tokens: int,
    temperature: float | None,
) -> dict[str, Any]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    return api_request(
        "POST",
        "/chat/completions",
        api_key=api_key,
        payload=payload,
    )


def response_text(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise OpenRouterError(
            "La resposta del model no conté cap missatge de text."
        ) from None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        if any(chunks):
            return "".join(chunks)
    raise OpenRouterError("El contingut retornat no és text compatible.")


def print_response_metadata(response: dict[str, Any]) -> None:
    model = response.get("model", "desconegut")
    usage = response.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}
    prompt_tokens = usage.get("prompt_tokens", "?")
    completion_tokens = usage.get("completion_tokens", "?")
    print(
        f"\n[OpenRouter] model={model}; "
        f"tokens_entrada={prompt_tokens}; tokens_sortida={completion_tokens}",
        file=sys.stderr,
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Consulta OpenRouter des de la zona de recerca, amb la clau al "
            "Clauer de macOS."
        )
    )
    parser.add_argument(
        "--keychain-service",
        help=(
            "servei alternatiu del Clauer; també es pot definir amb "
            "OPENROUTER_KEYCHAIN_SERVICE"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "check",
        help="valida la clau i mostra límits/ús sense gastar tokens",
    )

    ask_parser = subparsers.add_parser(
        "ask",
        help="envia una consulta explícita a un model",
    )
    ask_parser.add_argument("prompt", nargs="?", help="text de la consulta")
    ask_parser.add_argument(
        "--prompt-file",
        type=Path,
        help="fitxer UTF-8 que conté la consulta",
    )
    ask_parser.add_argument(
        "--context",
        action="append",
        default=[],
        type=Path,
        metavar="FITXER",
        help=(
            "afegeix un fitxer UTF-8 al prompt; el contingut s'enviarà al "
            "proveïdor seleccionat (repetible)"
        ),
    )
    ask_parser.add_argument(
        "--model",
        default=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        help=f"model d'OpenRouter (per defecte: {DEFAULT_MODEL})",
    )
    ask_parser.add_argument("--system", help="instrucció de sistema opcional")
    ask_parser.add_argument(
        "--max-tokens",
        type=int,
        default=1500,
        help="màxim de tokens de resposta (per defecte: 1500)",
    )
    ask_parser.add_argument(
        "--temperature",
        type=float,
        help="temperatura opcional; si s'omet, decideix el model",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        api_key = load_api_key(args.keychain_service)
        if args.command == "check":
            print_connection_summary(check_connection(api_key))
            return 0

        if args.max_tokens < 1:
            raise OpenRouterError("--max-tokens ha de ser com a mínim 1.")
        if args.temperature is not None and not 0 <= args.temperature <= 2:
            raise OpenRouterError("--temperature ha d'estar entre 0 i 2.")
        prompt = build_user_prompt(
            args.prompt,
            args.prompt_file,
            args.context,
        )
        response = ask(
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            system=args.system,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        print(response_text(response))
        print_response_metadata(response)
        return 0
    except OpenRouterError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterromput.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
