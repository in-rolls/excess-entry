"""Retrieve the published election inputs declared in data_sources.json."""

import hashlib
import json
import os
from pathlib import Path

import pooch

SOURCES = json.loads(
    (Path(__file__).resolve().parents[1] / "data_sources.json").read_text()
)


def source_path(name, local=None):
    spec = SOURCES[name]
    if local is not None:
        path = Path(local).expanduser()
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError(f"Source checksum mismatch: {path}")
        return path
    relative = Path(spec["path"])
    cache = Path(os.environ.get("INDIA_DATA_HOME", "~/data")).expanduser()
    return Path(
        pooch.retrieve(
            url=(
                f"https://raw.githubusercontent.com/in-rolls/{spec['provider']}/"
                f"{spec['ref']}/{spec['path']}"
            ),
            known_hash="sha256:" + spec["sha256"],
            path=cache / spec["provider"] / spec["ref"] / relative.parent,
            fname=relative.name,
        )
    )
