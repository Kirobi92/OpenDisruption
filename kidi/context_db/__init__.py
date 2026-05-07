"""
kidi/context_db/__init__.py
Zone: WORKSPACE

Public API des context_db-Pakets.
"""

from .client import ContextDB
from .errors import (
    ContextDBError,
    EgressViolation,
    KeyValueMismatch,
    SacredApprovalMissing,
    ZoneViolation,
)
from .keys import VALID_ZONES, ParsedKey, is_valid_key, make_key, parse_key
from .zone_guard import check_read, check_write, is_readable, zone_rank

__all__ = [
    # Client
    "ContextDB",
    # Keys
    "make_key",
    "parse_key",
    "is_valid_key",
    "ParsedKey",
    "VALID_ZONES",
    # Zone-Guard
    "check_read",
    "check_write",
    "is_readable",
    "zone_rank",
    # Errors
    "ContextDBError",
    "ZoneViolation",
    "EgressViolation",
    "KeyValueMismatch",
    "SacredApprovalMissing",
]
