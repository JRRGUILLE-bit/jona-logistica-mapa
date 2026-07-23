#!/usr/bin/env python3
"""Translate MetSul headlines and excerpts from Portuguese to Spanish.

The weather collector remains independent from the translation engine. This
script runs immediately afterwards, stores a small translation memory in the
repository, and leaves the original Portuguese text available as a fallback.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WEATHER_PATH = ROOT / "data" / "weather.json"
CACHE_PATH = ROOT / "data" / "metsul-translations.json"
SOURCE_CODE = "pt"
TARGET_CODE = "es"
MAX_CACHE_ENTRIES = 250


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def original_text(article: dict[str, Any], field: str) -> str:
    return str(
        article.get(f"{field}_pt")
        or article.get(f"{field}_original")
        or article.get(field)
        or ""
    ).strip()


def cache_key(title: str, excerpt: str) -> str:
    source = json.dumps(
        {"title": title, "excerpt": excerpt},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def installed_translation(from_code: str, to_code: str):
    import argostranslate.translate

    languages = argostranslate.translate.get_installed_languages()
    source = next((lang for lang in languages if lang.code == from_code), None)
    target = next((lang for lang in languages if lang.code == to_code), None)
    if source is None or target is None:
        return None
    try:
        return source.get_translation(target)
    except Exception:
        return None


def ensure_translation_model():
    translation = installed_translation(SOURCE_CODE, TARGET_CODE)
    if translation is not None:
        return translation

    import argostranslate.package

    print("Installing Argos Portuguese → Spanish model…")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    candidates = [
        package
        for package in available
        if package.from_code == SOURCE_CODE and package.to_code == TARGET_CODE
    ]
    if not candidates:
        raise RuntimeError("Argos no ofrece un modelo portugués → español")

    package = sorted(candidates, key=lambda item: item.package_version)[-1]
    argostranslate.package.install_from_path(package.download())
    translation = installed_translation(SOURCE_CODE, TARGET_CODE)
    if translation is None:
        raise RuntimeError("El modelo de Argos se instaló pero no quedó disponible")
    return translation


def safe_translate(translation, text: str) -> str:
    if not text:
        return ""
    result = str(translation.translate(text) or "").strip()
    # Guard against empty or pathological repetitive model output.
    if not result or len(result) > max(500, len(text) * 5):
        raise ValueError("La traducción automática produjo una salida inválida")
    return result


def translate_articles(
    articles: list[dict[str, Any]],
    entries: dict[str, dict[str, Any]],
    translation,
) -> tuple[int, int]:
    translated_count = 0
    cached_count = 0

    for article in articles:
        title_pt = original_text(article, "title")
        excerpt_pt = original_text(article, "excerpt")
        key = cache_key(title_pt, excerpt_pt)
        cached = entries.get(key)

        if cached and cached.get("title_pt") == title_pt and cached.get("excerpt_pt") == excerpt_pt:
            title_es = str(cached.get("title_es") or title_pt)
            excerpt_es = str(cached.get("excerpt_es") or excerpt_pt)
            cached_count += 1
        else:
            title_es = safe_translate(translation, title_pt)
            excerpt_es = safe_translate(translation, excerpt_pt) if excerpt_pt else ""
            entries[key] = {
                "title_pt": title_pt,
                "excerpt_pt": excerpt_pt,
                "title_es": title_es,
                "excerpt_es": excerpt_es,
            }
            translated_count += 1

        article.update(
            {
                "title_pt": title_pt,
                "excerpt_pt": excerpt_pt,
                "title": title_es or title_pt,
                "excerpt": excerpt_es or excerpt_pt,
                "language": "es",
                "original_language": "pt",
                "translation_status": "translated",
                "translation_engine": "Argos Translate",
            }
        )

    return translated_count, cached_count


def propagate_to_days(payload: dict[str, Any], source_articles: list[dict[str, Any]]) -> None:
    by_id = {str(article.get("id")): article for article in source_articles if article.get("id") is not None}
    by_url = {str(article.get("url")): article for article in source_articles if article.get("url")}

    for day in payload.get("days", []):
        translated: list[dict[str, Any]] = []
        for article in day.get("metsul_articles", []):
            match = by_id.get(str(article.get("id"))) or by_url.get(str(article.get("url")))
            translated.append(dict(match) if match else article)
        day["metsul_articles"] = translated


def prune_entries(entries: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if len(entries) <= MAX_CACHE_ENTRIES:
        return entries
    # JSON dictionaries preserve insertion order; retain the most recent items.
    return dict(list(entries.items())[-MAX_CACHE_ENTRIES:])


def main() -> int:
    payload = load_json(WEATHER_PATH, {})
    if not payload:
        print(f"No se encontró un weather.json válido en {WEATHER_PATH}", file=sys.stderr)
        return 0

    source = payload.setdefault("sources", {}).setdefault("metsul", {})
    articles = source.get("articles", [])
    if not articles:
        source["translation"] = {
            "status": "not-needed",
            "engine": "Argos Translate",
            "source_language": SOURCE_CODE,
            "target_language": TARGET_CODE,
        }
        write_json(WEATHER_PATH, payload)
        return 0

    cache = load_json(
        CACHE_PATH,
        {
            "schema_version": 1,
            "engine": "Argos Translate",
            "source_language": SOURCE_CODE,
            "target_language": TARGET_CODE,
            "entries": {},
        },
    )
    entries = cache.setdefault("entries", {})

    try:
        translation = ensure_translation_model()
        translated_count, cached_count = translate_articles(articles, entries, translation)
        propagate_to_days(payload, articles)
        source["translation"] = {
            "status": "ok",
            "engine": "Argos Translate",
            "source_language": SOURCE_CODE,
            "target_language": TARGET_CODE,
            "translated_now": translated_count,
            "from_cache": cached_count,
        }
        cache["entries"] = prune_entries(entries)
        write_json(CACHE_PATH, cache)
        print(
            f"MetSul: {translated_count} traducciones nuevas, "
            f"{cached_count} recuperadas del caché."
        )
    except Exception as exc:
        # Translation is an enhancement: never erase or block weather data.
        source["translation"] = {
            "status": "fallback",
            "engine": "Argos Translate",
            "source_language": SOURCE_CODE,
            "target_language": TARGET_CODE,
            "error": str(exc),
        }
        print(f"MetSul translation fallback: {exc}", file=sys.stderr)

    write_json(WEATHER_PATH, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
