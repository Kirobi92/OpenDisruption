"""Pytest configuration: make the repository root importable.

This avoids needing an installed package or ``PYTHONPATH`` tweaks when
running ``pytest`` from a fresh clone.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
