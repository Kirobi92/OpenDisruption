#!/usr/bin/env python3
"""Parse detect-system JSON for install.sh.

Reads the JSON emitted by infra/scripts/detect-system.sh --json on stdin and
prints tab-separated OS fields expected by install.sh:

    kernel<TAB>arch<TAB>name<TAB>version<TAB>family
"""

from __future__ import annotations

import json
import platform
import sys


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 1

    os_raw = data.get("os", {})
    os_data = os_raw if isinstance(os_raw, dict) else {}
    values = [
        str(data.get("kernel", "") or platform.system() or "unknown"),
        str(data.get("arch", "") or os_data.get("arch", "")),
        str(data.get("name", "") or os_data.get("name", "")),
        str(data.get("version", "") or os_data.get("version", "")),
        str(data.get("family", "") or os_data.get("family", "")),
    ]
    sys.stdout.write("\t".join(values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
