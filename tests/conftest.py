"""Pytest configuration: make the repository root importable.

This avoids needing an installed package or ``PYTHONPATH`` tweaks when
running ``pytest`` from a fresh clone.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _register_hyphenated_service(dir_name: str, module_name: str) -> None:
    """Registriert einen Service mit Bindestrich im Verzeichnisnamen als importierbares Modul.

    Beispiel: services/model-routing/main.py → services.model_routing.main
    """
    service_dir = _ROOT / "services" / dir_name
    if not service_dir.exists():
        return

    # Paket-Stub für services.<module_name> anlegen
    pkg_name = f"services.{module_name}"
    if pkg_name not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.util.spec_from_loader(pkg_name, loader=None, origin=str(service_dir))
        )
        pkg.__path__ = [str(service_dir)]  # type: ignore[attr-defined]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg

    # main.py des Service laden
    main_name = f"{pkg_name}.main"
    if main_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(main_name, service_dir / "main.py")
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            mod.__package__ = pkg_name
            sys.modules[main_name] = mod
            spec.loader.exec_module(mod)  # type: ignore[union-attr]


# services/model-routing → services.model_routing
_register_hyphenated_service("model-routing", "model_routing")
