#!/usr/bin/env python3
"""Dependency-free QA checks for the Jona static site."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    Path("index.html"), Path("404.html"), Path("clima/index.html"),
    Path("movilidad/index.html"), Path("supermercados/index.html"),
    Path("docs/index.html"), Path("apps/index.html"), Path("discord/index.html"),
]
REDIRECT = Path("links/index.html")


def local_target(source: Path, value: str) -> Path | None:
    value = value.strip()
    if not value or value.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or value.startswith("//"):
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    if path.startswith("/jona-logistica/"):
        target = ROOT / path.removeprefix("/jona-logistica/")
    elif path.startswith("/"):
        return None
    else:
        target = (ROOT / source.parent / path).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return Path("__outside_repo__")
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def check_page(path: Path) -> list[str]:
    errors: list[str] = []
    text = (ROOT / path).read_text(encoding="utf-8")
    required = {
        '<html lang="es">': "html language",
        'name="viewport"': "viewport",
        'name="description"': "description",
        'rel="canonical"': "canonical URL",
        'rel="manifest"': "web manifest",
        'offline.js?v=3': "offline bootstrap v3",
        'id="main-content"': "main content target",
        'property="og:image"': "Open Graph image",
        'name="twitter:card"': "Twitter card",
    }
    for needle, label in required.items():
        if needle not in text:
            errors.append(f"missing {label}")
    if not re.search(r"<title>\s*.+?\s*</title>", text, re.S):
        errors.append("missing title")
    if not re.search(r"<h1\b", text, re.I):
        errors.append("missing h1")
    if "\\n<" in text.split("</head>", 1)[0]:
        errors.append("literal backslash-n sequence in head")

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', text, re.I)
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append("duplicate ids: " + ", ".join(duplicates))

    for tag in re.findall(r"<a\b[^>]*>", text, re.I):
        if re.search(r'target=["\']_blank["\']', tag, re.I):
            rel = re.search(r'rel=["\']([^"\']*)["\']', tag, re.I)
            if not rel or "noopener" not in rel.group(1).split():
                errors.append("target=_blank link missing noopener")

    for tag in re.findall(r"<img\b[^>]*>", text, re.I):
        if not re.search(r'\balt=["\']', tag, re.I):
            errors.append("image missing alt attribute")

    for tag in re.findall(r"<button\b[^>]*>", text, re.I):
        if not re.search(r'\btype=["\']', tag, re.I):
            errors.append("button missing explicit type")

    for attr, value in re.findall(r'\b(href|src)=["\']([^"\']+)["\']', text, re.I):
        target = local_target(path, value)
        if target is not None and not target.exists():
            try:
                shown = target.relative_to(ROOT)
            except ValueError:
                shown = target
            errors.append(f"broken internal {attr}: {value} -> {shown}")
    return errors


def check_redirect() -> list[str]:
    text = (ROOT / REDIRECT).read_text(encoding="utf-8")
    errors = []
    if "../docs/" not in text:
        errors.append("links redirect does not target Docs")
    if 'rel="canonical"' not in text:
        errors.append("links redirect missing canonical")
    return errors


def check_manifest() -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid JSON: {exc}"]
    for key in ("name", "short_name", "id", "start_url", "scope", "display", "icons"):
        if not data.get(key):
            errors.append(f"missing {key}")
    sizes = set()
    for icon in data.get("icons", []):
        src = str(icon.get("src", "")).split("?", 1)[0]
        target = ROOT / src
        if not target.exists():
            errors.append(f"missing icon file: {src}")
        declared = str(icon.get("sizes", ""))
        sizes.add(declared)
        if target.suffix.lower() == ".svg" and declared != "any":
            errors.append(f"SVG icon must use sizes=any: {src}")
    if "192x192" not in sizes:
        errors.append("missing 192x192 install icon")
    if "any" not in sizes:
        errors.append("missing scalable install icon")
    return errors


def check_worker() -> list[str]:
    errors: list[str] = []
    text = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    if not re.search(r'const CACHE_NAME = `\$\{CACHE_PREFIX\}v5`;', text):
        errors.append("cache version is not v5")
    if "./offline.js?v=3" not in text:
        errors.append("offline.js v3 is not precached")
    for raw in re.findall(r"['\"](\./[^'\"]+)['\"]", text):
        clean = raw.split("?", 1)[0].removeprefix("./")
        target = ROOT / clean
        if clean.endswith("/") or target.is_dir():
            target = target / "index.html"
        if not target.exists():
            errors.append(f"missing precache target: {raw}")
    return errors


def main() -> int:
    failures: list[str] = []
    for path in PAGES:
        if not (ROOT / path).exists():
            failures.append(f"{path}: missing file")
            continue
        failures.extend(f"{path}: {item}" for item in check_page(path))
    failures.extend(f"{REDIRECT}: {item}" for item in check_redirect())
    failures.extend(f"manifest.webmanifest: {item}" for item in check_manifest())
    failures.extend(f"service-worker.js: {item}" for item in check_worker())

    if failures:
        print("SITE QA FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"SITE QA PASSED: {len(PAGES) + 1} pages, manifest and service worker checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
