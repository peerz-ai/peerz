import os
import platform

os.environ.setdefault("BITSANDBYTES_NOWELCOME", "1")

if platform.system() == "Darwin":
    # Necessary for forks to work properly on macOS, see https://github.com/kevlened/pytest-parallel/issues/93
    os.environ.setdefault("no_proxy", "*")
    os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

import hivemind
import transformers
from packaging import version

from peerz.client import *
from peerz.models import *
from peerz.utils import *
from peerz.utils.logging import initialize_logs as _initialize_logs

__version__ = "2.3.0.dev1"


if not os.getenv("PEERZ_IGNORE_DEPENDENCY_VERSION"):
    assert (
        version.parse("4.32.0") <= version.parse(transformers.__version__) < version.parse("4.35.0")
    ), "Please install a proper transformers version: pip install transformers>=4.32.0,<4.35.0"


def _override_bfloat16_mode_default():
    if os.getenv("USE_LEGACY_BFLOAT16") is None:
        hivemind.compression.base.USE_LEGACY_BFLOAT16 = False


_initialize_logs()
_override_bfloat16_mode_default()
