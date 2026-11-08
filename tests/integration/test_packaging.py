"""Exercise the generated launcher rather than importing the Click group directly."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def test_installed_launcher(tmp_path):
    """Build and install a wheel, then run its launcher without the build source."""
    source = Path(__file__).resolve().parents[2]
    project = tmp_path / "source"
    shutil.copytree(
        source,
        project,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "venv", "build", "dist", "*.egg-info", "__pycache__",
        ),
    )
    env = {
        key: value for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"} and not key.startswith("PORKBUN_")
    }
    env["HOME"] = str(tmp_path / "home")
    env["USERPROFILE"] = env["HOME"]
    Path(env["HOME"]).mkdir()

    def run(*args):
        """Run an isolated subprocess and report its output if it fails."""
        result = subprocess.run(
            args, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    wheels = tmp_path / "wheels"
    run(
        sys.executable, "-m", "pip", "wheel", "--no-deps",
        "--wheel-dir", str(wheels), str(project),
    )
    # Install the wheel and its declared dependencies into a clean environment.
    environment = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    run(
        str(python), "-m", "pip", "install",
        str(next(wheels.glob("*.whl"))),
    )
    # Removing the build source also catches accidental editable/source dependencies.
    shutil.rmtree(project)
    launcher = scripts / ("porkbun.exe" if os.name == "nt" else "porkbun")
    assert "Manage your domains and DNS records" in run(str(launcher), "--help")
    assert "Watch list is empty" in run(str(launcher), "domains", "watch-list")
