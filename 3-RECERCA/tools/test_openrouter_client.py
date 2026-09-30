#!/usr/bin/env python3

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parent))

import openrouter_client


class Completed:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return io.StringIO(json.dumps(self.payload))

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class OpenRouterClientTests(unittest.TestCase):
    def test_environment_key_has_priority(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "secret-from-env"},
            clear=True,
        ):
            with mock.patch.object(
                openrouter_client.subprocess,
                "run",
            ) as run:
                self.assertEqual(
                    openrouter_client.load_api_key(),
                    "secret-from-env",
                )
                run.assert_not_called()

    def test_keychain_fallback_returns_first_secret(self) -> None:
        results = [
            Completed(44),
            Completed(0, "secret-from-keychain\n"),
        ]
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(
                openrouter_client.subprocess,
                "run",
                side_effect=results,
            ):
                self.assertEqual(
                    openrouter_client.load_api_key(),
                    "secret-from-keychain",
                )

    def test_missing_key_does_not_expose_keychain_errors(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(
                openrouter_client.subprocess,
                "run",
                return_value=Completed(44),
            ):
                with self.assertRaises(openrouter_client.OpenRouterError) as caught:
                    openrouter_client.load_api_key()
        self.assertNotIn("secret", str(caught.exception).lower())

    def test_api_request_uses_bearer_without_printing_it(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse({"data": {"usage": 0}})

        with mock.patch.object(
            openrouter_client.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            response = openrouter_client.api_request(
                "GET",
                "/key",
                api_key="top-secret",
                timeout=30,
            )
        self.assertEqual(response["data"]["usage"], 0)
        self.assertEqual(captured["timeout"], 30)
        self.assertEqual(
            captured["request"].get_header("Authorization"),
            "Bearer top-secret",
        )

    def test_http_error_is_reduced_to_safe_message(self) -> None:
        error = urllib.error.HTTPError(
            "https://openrouter.ai/api/v1/key",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error":{"message":"Invalid API key"}}'),
        )
        message = openrouter_client._safe_api_error(error)
        self.assertEqual(
            message,
            "OpenRouter ha respost HTTP 401: Invalid API key",
        )

    def test_build_prompt_includes_explicit_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "context.txt")
            path.write_text("dades", encoding="utf-8")
            result = openrouter_client.build_user_prompt(
                "analitza",
                None,
                [path],
            )
        self.assertIn("analitza", result)
        self.assertIn("CONTEXT:", result)
        self.assertIn("dades", result)

    def test_prompt_and_prompt_file_are_mutually_exclusive(self) -> None:
        with self.assertRaises(openrouter_client.OpenRouterError):
            openrouter_client.build_user_prompt(
                "text",
                Path("prompt.txt"),
                [],
            )

    def test_response_text_accepts_string_and_text_parts(self) -> None:
        self.assertEqual(
            openrouter_client.response_text(
                {"choices": [{"message": {"content": "resposta"}}]}
            ),
            "resposta",
        )
        self.assertEqual(
            openrouter_client.response_text(
                {
                    "choices": [
                        {
                            "message": {
                                "content": [
                                    {"type": "text", "text": "res"},
                                    {"type": "text", "text": "posta"},
                                ]
                            }
                        }
                    ]
                }
            ),
            "resposta",
        )


if __name__ == "__main__":
    unittest.main()
