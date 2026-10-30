"""Shared helpers: import paths, environment isolation, CLI/hook runners, fake secrets."""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import finops_hook  # noqa: E402
import guard  # noqa: E402
import oeo  # noqa: E402

__all__ = ["ROOT", "SCRIPTS", "oeo", "guard", "finops_hook", "IsolatedTestCase", "fake_secrets", "subprocess_env"]

_ENV_PREFIXES = ("OEO_",)
_ENV_NAMES = ("CLAUDE_PROJECT_DIR",)


def _is_oeo_env(name):
    return name.startswith(_ENV_PREFIXES) or name in _ENV_NAMES


def subprocess_env(**extra):
    """Environment for a child process: no OEO_*/CLAUDE_PROJECT_DIR leakage from the caller."""
    env = {k: v for k, v in os.environ.items() if not _is_oeo_env(k)}
    env.update(extra)
    return env


def fake_secrets():
    """Secret-shaped strings assembled at runtime so no literal token exists in source.

    Returns {guard kind label: value}. The label is the text the guard puts in its reason.
    """
    return {
        "AWS access key id": "AK" + "IA" + "A" * 16,
        "private key": "-----BEGIN " + "PRIVATE KEY-----",
        "GitHub token": "gh" + "p_" + "a" * 36,
        "Slack token": "xo" + "xb-" + "1234567890" + "abcdef",
        "Anthropic API key": "sk-" + "ant-" + "a" * 30,
        "OpenAI-style API key": "sk-" + "a" * 40,
        "Google API key": "AI" + "za" + "a" * 35,
        "Stripe live key": "sk" + "_live_" + "a" * 24,
    }


class IsolatedTestCase(unittest.TestCase):
    """Per-test temp dir + a clean OEO environment.

    CLAUDE_PROJECT_DIR points at the temp dir by default, so even a test that forgets to
    set it can never log into the repository.
    """

    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in [n for n in os.environ if _is_oeo_env(n)]:
            del os.environ[name]
        self.tmp = Path(tempfile.mkdtemp(prefix="oeo-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.tmp)

    # -- runners ---------------------------------------------------------------------------
    def run_cli(self, *argv):
        """Run oeo.main(argv). Returns (exit_code_or_None, stdout, stderr); SystemExit is caught."""
        out, err, code = io.StringIO(), io.StringIO(), None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                oeo.main(list(argv))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def run_hook(self, module, stdin_text):
        """Run a hook's main() with patched stdin/stdout. Returns (return_code, stdout)."""
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(stdin_text)), mock.patch.object(sys, "stdout", out):
            rc = module.main()
        return rc, out.getvalue()
