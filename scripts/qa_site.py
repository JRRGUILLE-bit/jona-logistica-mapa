#!/usr/bin/env python3
"""Static QA and deterministic fixes for the Jona production site."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://jrrguille-bit.github.io/jona-logistica/"
SOCIAL_IMAGE = f"{BASE_URL}social-preview-jona-1200x630.jpg"
HTML_FILES = [
    Path("index.html"),
    Path("404.html"),
    Path("clima/index.html"),
    Path("movilidad/index.html"),
    Path("supermercados/index.html"),
    Path("docs/index.html"),
    Path("apps/index.html"),
    Path("discord/index.html"),
    Path("links/index.html"),
]
REDIRECT_PAGES = {Path("links/index.html")}


def read(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write_if_changed(path: Path, content: str) -> bool:
    target = ROOT / path
    original = target.read_text(encoding="utf-8")
    if original == content:
        return False
    target.write_text(content, encoding="utf-8", newline="\n")
    print(f"fixed: {path.as_posix()}")
    return True


def add_after_theme(content: str, block: str) -> str:
    marker = re.search(r'<meta name="theme-color"[^>]*>\s*', content)
    if not marker:
        return content
    return content[: marker.end()] + block + content[marker.end() :]


def social_block(title: str, description: str, canonical: str) -> str:
    return (
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{description}">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:url" content="{canonical}">\n'
        f'<meta property="og:image" content="{SOCIAL_IMAGE}">\n'
        f'<meta property="og:image:secure_url" content="{SOCIAL_IMAGE}">\n'
        '<meta property="og:image:type" content="image/jpeg">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="{title}">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{title}">\n'
        f'<meta name="twitter:description" content="{description}">\n'
        f'<meta name="twitter:image" content="{SOCIAL_IMAGE}">\n'
        f'<meta name="twitter:image:alt" content="{title}">\n'
    )


def ensure_blank_rel(tag: str) -> str:
    if not re.search(r'target\s*=\s*["\']_blank["\']', tag, re.I):
        return tag
    rel_match = re.search(r'rel\s*=\s*(["\'])(.*?)\1', tag, re.I)
    if rel_match:
        values = rel_match.group(2).split()
        for value in ("noopener", "noreferrer"):
            if value not in values:
                values.append(value)
        replacement = f'rel={rel_match.group(1)}{" ".join(values)}{rel_match.group(1)}'
        return tag[: rel_match.start()] + replacement + tag[rel_match.end() :]
    return tag[:-1] + ' rel="noopener noreferrer">'


def fix_html(path: Path, content: str) -> str:
    if "</head>" not in content:
        return content

    head, tail = content.split("</head>", 1)
    # A previous generated edit left visible backslash-n sequences in Clima metadata.
    head = head.replace("\\n<", "\n<")
    content = head + "</head>" + tail

    if path not in REDIRECT_PAGES:
        common_meta = (
            '<meta name="color-scheme" content="dark">\n'
            '<meta name="mobile-web-app-capable" content="yes">\n'
            '<meta name="apple-mobile-web-app-capable" content="yes">\n'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
            '<meta name="apple-mobile-web-app-title" content="Jona Ops">\n'
            '<meta name="format-detection" content="telephone=no">\n'
        )
        if 'name="color-scheme"' not in content:
            content = add_after_theme(content, common_meta)

        prefix = "" if path.parent == Path(".") else "../"
        manifest_href = f"{prefix}manifest.webmanifest"
        if 'rel="manifest"' not in content:
            content = content.replace(
                "</head>", f'<link rel="manifest" href="{manifest_href}">\n</head>', 1
            )

        if "android-chrome-192x192.png" not in content:
            icon = f'<link rel="icon" type="image/png" sizes="192x192" href="{prefix}android-chrome-192x192.png">\n'
            apple = re.search(r'<link rel="apple-touch-icon"[^>]*>\s*', content)
            if apple:
                content = content[: apple.end()] + icon + content[apple.end() :]

        script_src = f"{prefix}offline.js?v=3"
        if re.search(r'<script[^>]+src=["\'][^"\']*offline\.js', content):
            content = re.sub(
                r'(<script[^>]+src=["\'])[^"\']*offline\.js(?:\?v=\d+)?(["\'])',
                rf'\1{script_src}\2',
                content,
                count=1,
            )
        else:
            content = content.replace(
                "</head>", f'<script defer src="{script_src}"></script>\n</head>', 1
            )

        if 'id="main-content"' not in content:
            content = re.sub(r"<main(\s+)", r'<main id="main-content"\1', content, count=1)

        title_match = re.search(r"<title>(.*?)</title>", content, re.S)
        desc_match = re.search(r'<meta name="description" content="([^"]*)">', content)
        canonical_match = re.search(r'<link rel="canonical" href="([^"]*)">', content)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else "Jona tenía 15 años"
        description = desc_match.group(1) if desc_match else "Base de operaciones del rodaje de Jona tenía 15 años."
        canonical = canonical_match.group(1) if canonical_match else BASE_URL

        if 'property="og:title"' not in content:
            insertion = social_block(title, description, canonical)
            content = content.replace(f"<title>{title_match.group(1)}</title>", insertion + f"<title>{title_match.group(1)}</title>", 1)
        else:
            missing = []
            if 'property="og:image"' not in content:
                missing.extend([
                    f'<meta property="og:image" content="{SOCIAL_IMAGE}">',
                    f'<meta property="og:image:secure_url" content="{SOCIAL_IMAGE}">',
                    '<meta property="og:image:type" content="image/jpeg">',
                    '<meta property="og:image:width" content="1200">',
                    '<meta property="og:image:height" content="630">',
                    f'<meta property="og:image:alt" content="{title}">',
                ])
            if 'name="twitter:card"' not in content:
                missing.extend([
                    '<meta name="twitter:card" content="summary_large_image">',
                    f'<meta name="twitter:title" content="{title}">',
                    f'<meta name="twitter:description" content="{description}">',
                    f'<meta name="twitter:image" content="{SOCIAL_IMAGE}">',
                    f'<meta name="twitter:image:alt" content="{title}">',
                ])
            if missing:
                marker = re.search(r'<meta property="og:url"[^>]*>\s*', content)
                if marker:
                    content = content[: marker.end()] + "\n".join(missing) + "\n" + content[marker.end() :]

    content = re.sub(r"<a\b[^>]*>", lambda match: ensure_blank_rel(match.group(0)), content, flags=re.I)

    if path == Path("supermercados/index.html"):
        content = content.replace(
            '<nav class="tabs">',
            '<nav class="tabs" role="tablist" aria-label="Filtrar lugares">',
        )
        content = content.replace(
            '<button class="tab active" data-filter="Todos">',
            '<button type="button" class="tab active" role="tab" aria-selected="true" data-filter="Todos">',
        )
        for label in ("Supermercado", "Almacén", "Farmacia"):
            content = content.replace(
                f'<button class="tab" data-filter="{label}">',
                f'<button type="button" class="tab" role="tab" aria-selected="false" data-filter="{label}">',
            )
        old = "document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));btn.classList.add('active');render(btn.dataset.filter)}));render();"
        new = "document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(b=>{b.classList.remove('active');b.setAttribute('aria-selected','false')});btn.classList.add('active');btn.setAttribute('aria-selected','true');render(btn.dataset.filter)}));render();"
        content = content.replace(old, new)

    return content


def fix_offline_js(content: str) -> str:
    marker = "  document.head.appendChild(style);\n"
    injection = """

  const mainContent = document.querySelector('main');
  if (mainContent) {
    if (!mainContent.id) mainContent.id = 'main-content';
    if (!document.querySelector('.skip-link')) {
      const skipLink = document.createElement('a');
      skipLink.className = 'skip-link';
      skipLink.href = `#${mainContent.id}`;
      skipLink.textContent = 'Saltar al contenido';
      document.body.prepend(skipLink);
    }
  }
"""
    if "const mainContent = document.querySelector('main');" not in content:
        content = content.replace(marker, marker + injection, 1)
    return content


def fix_manifest(content: str) -> str:
    data = json.loads(content)
    data["prefer_related_applications"] = False
    for collection in (data.get("icons", []),):
        for icon in collection:
            if str(icon.get("src", "")).lower().endswith(".svg"):
                icon["sizes"] = "any"
    for shortcut in data.get("shortcuts", []):
        for icon in shortcut.get("icons", []):
            if str(icon.get("src", "")).lower().endswith(".svg"):
                icon["sizes"] = "any"
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def fix_service_worker(content: str) -> str:
    content = re.sub(r"jona-offline-v\d+", "jona-offline-v5", content)
    content = content.replace("./offline.js?v=2", "./offline.js?v=3")
    if "./app-icon-512.svg" not in content:
        content = content.replace("  './android-chrome-192x192.png',", "  './android-chrome-192x192.png',\n  './app-icon-512.svg',")
    return content


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


def check_html(path: Path, content: str) -> list[str]:
    errors: list[str] = []
    redirect = path in REDIRECT_PAGES
    if '<html lang="es">' not in content:
        errors.append("missing html lang=es")
    if not re.search(r"<title>\s*.+?\s*</title>", content, re.S):
        errors.append("missing title")
    if 'name="viewport"' not in content:
        errors.append("missing viewport")
    if not redirect:
        for needle, label in [
            ('name="description"', "description"),
            ('rel="canonical"', "canonical"),
            ('rel="manifest"', "manifest"),
            ("offline.js?v=3", "offline bootstrap"),
            ('id="main-content"', "main-content target"),
            ('property="og:image"', "Open Graph image"),
            ('name="twitter:card"', "Twitter card"),
        ]:
            if needle not in content:
                errors.append(f"missing {label}")
        if not re.search(r"<h1\b", content, re.I):
            errors.append("missing h1")
    if "\\n<" in content.split("</head>", 1)[0]:
        errors.append("literal \\n sequence in head")

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', content, re.I)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        errors.append(f"duplicate ids: {', '.join(duplicates)}")

    for tag in re.findall(r"<a\b[^>]*>", content, re.I):
        if re.search(r'target\s*=\s*["\']_blank["\']', tag, re.I):
            rel = re.search(r'rel\s*=\s*["\']([^"\']*)["\']', tag, re.I)
            if not rel or "noopener" not in rel.group(1).split():
                errors.append(f"target=_blank without noopener: {tag[:100]}")

    for tag in re.findall(r"<img\b[^>]*>", content, re.I):
        if not re.search(r'\balt\s*=\s*["\']', tag, re.I):
            errors.append(f"img without alt: {tag[:100]}")

    for tag in re.findall(r"<button\b[^>]*>", content, re.I):
        if not re.search(r'\btype\s*=\s*["\']', tag, re.I):
            errors.append(f"button without explicit type: {tag[:100]}")

    for attr, value in re.findall(r'\b(href|src)=["\']([^"\']+)["\']', content, re.I):
        target = local_target(path, value)
        if target is not None and not target.exists():
            try:
                shown = target.relative_to(ROOT)
            except ValueError:
                shown = target
            errors.append(f"broken internal {attr}: {value} -> {shown}")
    return errors


def check_manifest() -> list[str]:
    errors: list[str] = []
    path = ROOT / "manifest.webmanifest"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"manifest.webmanifest: invalid JSON: {exc}"]
    for key in ("name", "short_name", "start_url", "scope", "display", "icons"):
        if not data.get(key):
            errors.append(f"manifest.webmanifest: missing {key}")
    for icon in data.get("icons", []):
        target = ROOT / str(icon.get("src", "")).split("?", 1)[0]
        if not target.exists():
            errors.append(f"manifest.webmanifest: missing icon {icon.get('src')}")
        if target.suffix.lower() == ".svg" and icon.get("sizes") != "any":
            errors.append(f"manifest.webmanifest: SVG icon must declare sizes=any: {icon.get('src')}")
    return errors


def check_service_worker() -> list[str]:
    errors: list[str] = []
    content = read(Path("service-worker.js"))
    if "jona-offline-v5" not in content:
        errors.append("service-worker.js: cache version is not v5")
    for raw in re.findall(r"['\"](\./[^'\"]+)['\"]", content):
        path = raw.split("?", 1)[0].removeprefix("./")
        target = ROOT / path
        if path.endswith("/") or target.is_dir():
            target = target / "index.html"
        if not target.exists():
            errors.append(f"service-worker.js: missing precache target {raw}")
    return errors


def run_fix() -> None:
    for path in HTML_FILES:
        write_if_changed(path, fix_html(path, read(path)))
    write_if_changed(Path("offline.js"), fix_offline_js(read(Path("offline.js"))))
    write_if_changed(Path("manifest.webmanifest"), fix_manifest(read(Path("manifest.webmanifest"))))
    write_if_changed(Path("service-worker.js"), fix_service_worker(read(Path("service-worker.js"))))


def run_checks() -> int:
    failures: list[str] = []
    for path in HTML_FILES:
        if not (ROOT / path).exists():
            failures.append(f"{path}: file missing")
            continue
        for error in check_html(path, read(path)):
            failures.append(f"{path}: {error}")
    failures.extend(check_manifest())
    failures.extend(check_service_worker())

    if failures:
        print("QA FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"QA passed: {len(HTML_FILES)} HTML pages, manifest and service worker checked.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="apply deterministic QA fixes before checking")
    args = parser.parse_args()
    if args.fix:
        run_fix()
    return run_checks()


if __name__ == "__main__":
    sys.exit(main())
