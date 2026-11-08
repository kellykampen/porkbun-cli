"""Library imports must be safe with Loguru's default DEBUG sink."""

import os
from pathlib import Path
import subprocess
import sys


def test_api_request_does_not_log_credentials(tmp_path):
    """Capture default DEBUG logs without inherited credentials or Loguru settings."""
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("PORKBUN_", "LOGURU_"))
    }
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    result = subprocess.run(
        [sys.executable, "-c", """
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import httpx
from porkbun.api import APIClient, config_manager

async def exercise():
    profile = SimpleNamespace(
        api_key='synthetic-api-credential', secret_key='synthetic-secret-credential',
        base_url='https://example.invalid/api',
    )
    response = httpx.Response(200, json={'status': 'SUCCESS'},
                              request=httpx.Request('POST', 'https://example.invalid/api/ping'))
    async with APIClient() as client:
        with patch.object(config_manager, 'get_profile', return_value=profile), \
             patch.object(client.client, 'request', new=AsyncMock(return_value=response)) as request:
            assert await client.request('ping', {'note': 'private-payload'}) == {'status': 'SUCCESS'}
            assert request.call_args.kwargs['json']['apikey'] == profile.api_key
            assert request.call_args.kwargs['json']['secretapikey'] == profile.secret_key

asyncio.run(exercise())
"""],
        env=env, cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    logs = result.stdout + result.stderr
    assert "Making API request" in logs
    for private_value in ("synthetic-api-credential", "synthetic-secret-credential",
                          "syntheti", "private-payload"):
        assert private_value not in logs
