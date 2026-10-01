#!/usr/bin/env python3
"""Read and update a Docker-style .env file without executing it as shell code."""

from __future__ import annotations

import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Tuple

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ASSIGN_RE = re.compile(
    r"^([ \t]*(?:export[ \t]+)?)([A-Za-z_][A-Za-z0-9_]*)([ \t]*=[ \t]*)(.*?)(\r?\n)?$"
)
INLINE_COMMENT_RE = re.compile(r"\s+#")


def _parse_value(raw: str, line_number: int) -> str:
    value = raw.strip()
    if not value:
        return ""

    if value[0] == "'":
        content = []
        index = 1
        closing = None
        while index < len(value):
            char = value[index]
            if char == "\\" and index + 1 < len(value) and value[index + 1] == "'":
                content.append("'")
                index += 2
                continue
            if char == "'":
                closing = index
                break
            content.append(char)
            index += 1
        if closing is None:
            raise ValueError("linha %d: aspas não fechadas no .env" % line_number)
        remainder = value[closing + 1 :].strip()
        if remainder and not remainder.startswith("#"):
            raise ValueError("linha %d: conteúdo após valor entre aspas" % line_number)
        return "".join(content)

    if value[0] == '"':
        escaped = False
        closing = None
        for index in range(1, len(value)):
            char = value[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                closing = index
                break
        if closing is None:
            raise ValueError("linha %d: aspas não fechadas no .env" % line_number)
        remainder = value[closing + 1 :].strip()
        if remainder and not remainder.startswith("#"):
            raise ValueError("linha %d: conteúdo após valor entre aspas" % line_number)
        try:
            return json.loads(value[: closing + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("linha %d: valor entre aspas inválido: %s" % (line_number, exc))

    comment = INLINE_COMMENT_RE.search(value)
    if comment:
        value = value[: comment.start()].rstrip()
    return value


def parse_env_text(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE entries; values are literal (no shell expansion)."""
    result: Dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].lstrip()
        if "=" not in stripped:
            raise ValueError("linha %d: esperada uma atribuição KEY=VALUE" % line_number)
        key, raw = stripped.split("=", 1)
        key = key.strip()
        if not KEY_RE.fullmatch(key):
            raise ValueError("linha %d: nome de variável inválido" % line_number)
        result[key] = _parse_value(raw, line_number)
    return result


def read_env(path: Path) -> Dict[str, str]:
    return parse_env_text(path.read_text(encoding="utf-8-sig"))


def _encode_value(value: str) -> str:
    if "\n" in value or "\r" in value or "\0" in value:
        raise ValueError("valores .env não podem conter quebras de linha ou NUL")
    if value == "":
        return ""
    # Docker Compose treats single-quoted values literally. The parser above
    # supports its escaped apostrophe form, avoiding interpolation of '$'.
    return "'" + value.replace("'", "\\'") + "'"


def update_env(path: Path, updates: Dict[str, str]) -> None:
    if not updates:
        return
    for key, value in updates.items():
        if not KEY_RE.fullmatch(key):
            raise ValueError("nome de variável inválido: %r" % key)
        if not isinstance(value, str):
            value = str(value)
        _encode_value(value)  # Validate before touching the file.

    original = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    lines = original.splitlines(keepends=True)
    found = set()
    result = []

    for line in lines:
        match = ASSIGN_RE.match(line)
        if match and match.group(2) in updates:
            key = match.group(2)
            eol = match.group(5) or "\n"
            result.append(match.group(1) + key + match.group(3) + _encode_value(str(updates[key])) + eol)
            found.add(key)
        else:
            result.append(line)

    if result and not result[-1].endswith(("\n", "\r")) and (set(updates) - found):
        result[-1] += "\n"
    for key in updates:
        if key not in found:
            result.append("%s=%s\n" % (key, _encode_value(str(updates[key]))))

    path.parent.mkdir(parents=True, exist_ok=True)
    old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    sensitive = any(
        key.endswith(("_TOKEN", "_PASSWORD", "_SECRET", "_KEY")) for key in updates
    )
    new_mode = 0o600 if sensitive else old_mode
    fd, temp_name = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write("".join(result))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, new_mode)
        os.replace(temp_name, str(path))
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise

def _cli(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) == 2 and args[0] == "export0":
        values = read_env(Path(args[1]))
        output = sys.stdout.buffer
        for key, value in values.items():
            output.write(key.encode("utf-8") + b"\0" + value.encode("utf-8") + b"\0")
        return 0

    if len(args) == 2 and args[0] == "set0":
        parts = sys.stdin.buffer.read().split(b"\0")
        if len(parts) < 3 or parts[-1] != b"" or (len(parts) - 1) % 2 != 0:
            raise ValueError("entrada set0 inválida: esperados pares chave\0valor\0")
        updates = {}
        for index in range(0, len(parts) - 1, 2):
            key = parts[index].decode("utf-8")
            value = parts[index + 1].decode("utf-8")
            updates[key] = value
        update_env(Path(args[1]), updates)
        return 0

    print("Uso: envfile.py export0 PATH | set0 PATH (entrada: pares KEY\\0VALUE\\0)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(_cli(sys.argv[1:]))
    except (OSError, UnicodeError, ValueError) as exc:
        print("[ERRO]: %s" % exc, file=sys.stderr)
        raise SystemExit(1)
