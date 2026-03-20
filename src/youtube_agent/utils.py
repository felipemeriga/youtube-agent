from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:50].rstrip("-")


def get_output_dir(base_dir: str, label: str) -> Path:
    today = date.today().isoformat()
    slug = slugify(label)
    out = Path(base_dir) / f"{today}-{slug}"
    counter = 2
    original = out
    while out.exists():
        out = Path(f"{original}-{counter}")
        counter += 1
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def save_text(path: Path, text: str) -> None:
    path.write_text(text)
