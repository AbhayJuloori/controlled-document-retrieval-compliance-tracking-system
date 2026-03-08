from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-_/]+")


def stable_uuid(value: str) -> UUID:
    return uuid5(NAMESPACE_URL, value)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]

