"""Local profile / configuration storage for Kirobi Core.

Profiles live as JSON files under ``.kirobi/profiles/`` (gitignored by
default — callers should ensure the directory is in ``.gitignore``).
The schema is intentionally small and forward-compatible: unknown keys
are preserved on read/write.

Sensitive answers from the interview are stored in a separate file
under the requested security zone. Only the *non-sensitive* summary
ends up in the default profile.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .zones import Zone

DEFAULT_CONFIG_DIR = Path(".kirobi")
PROFILES_SUBDIR = "profiles"
DEFAULT_PROFILE_NAME = "default"


@dataclass
class Profile:
    """In-memory representation of a Kirobi user / family profile."""

    name: str = DEFAULT_PROFILE_NAME
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    # Non-sensitive interview answers and derived preferences.
    answers: dict[str, Any] = field(default_factory=dict)
    # Derived configuration: priorities, agent preferences, quiet hours, …
    derived: dict[str, Any] = field(default_factory=dict)
    # Pointer (relative path) to a sensitive answers file, if any.
    sensitive_ref: str | None = None
    # Zone the sensitive_ref file lives in.
    sensitive_zone: str | None = None

    def merge_answers(self, new_answers: Mapping[str, Any]) -> None:
        """Merge new answers, refreshing the ``updated_at`` timestamp."""
        self.answers.update(new_answers)
        self.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConfigStore:
    """Filesystem-backed profile store.

    Parameters
    ----------
    repo_root:
        Repository root. Profiles will be written under
        ``repo_root / .kirobi / profiles``.
    """

    def __init__(self, repo_root: Path | str = ".") -> None:
        self.repo_root = Path(repo_root)
        self.config_dir = self.repo_root / DEFAULT_CONFIG_DIR
        self.profiles_dir = self.config_dir / PROFILES_SUBDIR

    # ---------------------------------------------------------------- IO
    def _profile_path(self, name: str) -> Path:
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_")) or DEFAULT_PROFILE_NAME
        return self.profiles_dir / f"{safe}.json"

    def ensure_dirs(self) -> None:
        """Create config directories if they don't exist."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name: str = DEFAULT_PROFILE_NAME) -> Profile:
        """Load a profile by name, returning a fresh one if missing."""
        path = self._profile_path(name)
        if not path.exists():
            return Profile(name=name)
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        # Forward-compatible: only pass known fields, keep the rest in answers.
        known = {"name", "created_at", "updated_at", "answers", "derived",
                 "sensitive_ref", "sensitive_zone"}
        kwargs = {k: raw.get(k) for k in known if k in raw}
        kwargs.setdefault("name", name)
        extras = {k: v for k, v in raw.items() if k not in known}
        prof = Profile(**kwargs)
        if extras:
            prof.answers.setdefault("_extra", {}).update(extras)
        return prof

    def save(self, profile: Profile) -> Path:
        """Persist *profile* to disk and return the file path."""
        self.ensure_dirs()
        profile.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        path = self._profile_path(profile.name)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(profile.to_dict(), fh, indent=2, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
        return path

    # -------------------------------------------------------- sensitive
    def write_sensitive(
        self,
        profile: Profile,
        payload: Mapping[str, Any],
        *,
        zone: Zone = Zone.FAMILY_PRIVATE,
    ) -> Path:
        """Write sensitive answers to a zoned sub-folder.

        Returns the path that was written. The path is stored on
        ``profile.sensitive_ref`` so callers can find it later. The
        contents themselves are *never* echoed into the main profile
        file.
        """
        zone_dir_map = {
            Zone.FAMILY_PRIVATE: self.repo_root / "extracts" / "family-private" / "profiles",
            Zone.SACRED: self.repo_root / "sacred" / "profiles",
            Zone.WORKSPACE: self.repo_root / "extracts" / "workspace" / "profiles",
        }
        target_dir = zone_dir_map.get(zone)
        if target_dir is None:
            raise ValueError(f"Unsupported sensitive zone: {zone!r}")
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{profile.name}.sensitive.json"
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(dict(payload), fh, indent=2, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
        try:
            rel = path.resolve().relative_to(self.repo_root.resolve())
            profile.sensitive_ref = str(rel).replace("\\", "/")
        except ValueError:
            profile.sensitive_ref = str(path)
        profile.sensitive_zone = zone.value
        return path
