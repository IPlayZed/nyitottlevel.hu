#!/usr/bin/env python3
"""Run screenshot-heavy Playwright suites in isolated parallel shards."""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import os
import pathlib
import subprocess
import sys
import time


ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = {
    "mobile": {
        "module": "tests.test_mobile_profiles",
        "artifact_dir": ROOT / "test-artifacts" / "mobile",
        "default_workers": 8,
        "maximum_shards": 60,
    },
    "desktop": {
        "module": "tests.test_desktop_profiles",
        "artifact_dir": ROOT / "test-artifacts" / "desktop",
        "default_workers": 5,
        "maximum_shards": 5,
    },
    "firefox": {
        "module": "tests.test_firefox_profiles",
        "artifact_dir": ROOT / "test-artifacts" / "firefox",
        "default_workers": 5,
        "maximum_shards": 5,
    },
}


def run_shard(target: str, shard_index: int, shard_count: int) -> tuple[int, subprocess.CompletedProcess[str]]:
    config = TARGETS[target]
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONUNBUFFERED": "1",
            "VISUAL_TEST_SHARD_INDEX": str(shard_index),
            "VISUAL_TEST_SHARD_COUNT": str(shard_count),
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "unittest", config["module"], "-v"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    return shard_index, result


def write_review_gallery(target: str, profiles: list[dict]) -> pathlib.Path:
    artifact_dir = TARGETS[target]["artifact_dir"]
    state_names = []
    for profile in profiles:
        for state_name in profile["screenshots"]:
            if state_name not in state_names:
                state_names.append(state_name)

    sections = []
    for state_name in state_names:
        figures = []
        for profile in profiles:
            screenshot = profile["screenshots"].get(state_name)
            if not screenshot:
                continue
            source = os.path.relpath(ROOT / screenshot, artifact_dir)
            viewport = profile["viewport"]
            caption = f"{profile['name']} · {viewport['width']}×{viewport['height']}"
            figures.append(
                "<figure>"
                f'<a href="{html.escape(source, quote=True)}"><img loading="lazy" src="{html.escape(source, quote=True)}" alt=""></a>'
                f"<figcaption>{html.escape(caption)}</figcaption>"
                "</figure>"
            )
        sections.append(
            f'<section id="{html.escape(state_name, quote=True)}">'
            f"<h2>{html.escape(state_name.replace('_', ' ').title())}</h2>"
            f'<div class="grid">{"".join(figures)}</div>'
            "</section>"
        )

    document = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(target.title())} visual QA gallery</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; background: #172b2c; color: #fff; font: 15px/1.45 system-ui, sans-serif; }}
  h1 {{ margin: 0 0 32px; }} h2 {{ margin-top: 48px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill,minmax(240px,1fr)); gap: 18px; align-items: start; }}
  figure {{ margin: 0; padding: 10px; border-radius: 10px; background: #fff; color: #172b2c; }}
  img {{ display: block; width: 100%; height: auto; border: 1px solid #cad4d2; }}
  figcaption {{ padding-top: 8px; font-weight: 700; }}
</style>
<body><h1>{html.escape(target.title())} visual QA gallery</h1>{''.join(sections)}</body>
</html>
"""
    destination = artifact_dir / "review.html"
    temporary = destination.with_suffix(".html.tmp")
    temporary.write_text(document, encoding="utf-8")
    temporary.replace(destination)
    return destination


def merge_manifests(target: str, shard_count: int, elapsed_seconds: float) -> tuple[pathlib.Path, pathlib.Path]:
    artifact_dir = TARGETS[target]["artifact_dir"]
    manifests = []
    for shard_index in range(shard_count):
        path = artifact_dir / f"manifest-shard-{shard_index + 1}-of-{shard_count}.json"
        if not path.exists():
            raise RuntimeError(f"Missing shard manifest: {path}")
        manifests.append(json.loads(path.read_text(encoding="utf-8")))

    total_counts = {manifest["total_profile_count"] for manifest in manifests}
    if len(total_counts) != 1:
        raise RuntimeError(f"Shard manifests disagree about total profiles: {sorted(total_counts)}")

    profiles = sorted(
        (profile for manifest in manifests for profile in manifest["profiles"]),
        key=lambda profile: profile["profile_index"],
    )
    expected_count = total_counts.pop()
    if len(profiles) != expected_count:
        raise RuntimeError(f"Expected {expected_count} profiles but merged {len(profiles)}")
    if len({profile["profile_index"] for profile in profiles}) != expected_count:
        raise RuntimeError("Merged profile indexes are not unique")

    merged = {
        "description": manifests[0]["description"],
        "profile_count": len(profiles),
        "parallel_workers": shard_count,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "profiles": profiles,
    }
    destination = artifact_dir / "manifest.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(destination)
    return destination, write_review_gallery(target, profiles)


def run_target(target: str, requested_workers: int | None) -> None:
    config = TARGETS[target]
    shard_count = min(requested_workers or config["default_workers"], config["maximum_shards"])
    config["artifact_dir"].mkdir(parents=True, exist_ok=True)
    for stale_manifest in config["artifact_dir"].glob("manifest-shard-*.json"):
        stale_manifest.unlink()

    started = time.monotonic()
    failures: list[tuple[int, subprocess.CompletedProcess[str]]] = []
    print(f"Running {target} visual tests in {shard_count} isolated processes…", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=shard_count) as executor:
        futures = {
            executor.submit(run_shard, target, shard_index, shard_count): shard_index
            for shard_index in range(shard_count)
        }
        for future in concurrent.futures.as_completed(futures):
            shard_index, result = future.result()
            status = "PASS" if result.returncode == 0 else "FAIL"
            print(f"  shard {shard_index + 1}/{shard_count}: {status}", flush=True)
            if result.returncode != 0:
                failures.append((shard_index, result))

    if failures:
        for shard_index, result in sorted(failures):
            print(f"\n--- {target} shard {shard_index + 1} stdout ---\n{result.stdout}", file=sys.stderr)
            print(f"\n--- {target} shard {shard_index + 1} stderr ---\n{result.stderr}", file=sys.stderr)
        raise SystemExit(1)

    elapsed = time.monotonic() - started
    manifest_path, gallery_path = merge_manifests(target, shard_count, elapsed)
    print(f"Merged {target} manifest: {manifest_path.relative_to(ROOT)} ({elapsed:.1f}s)", flush=True)
    print(f"Batch review gallery: {gallery_path.relative_to(ROOT)}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=(*TARGETS, "all"), nargs="?", default="all")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="maximum isolated browser processes per suite (default: 8 mobile, 5 desktop, 5 Firefox)",
    )
    args = parser.parse_args()
    if args.workers is not None and args.workers < 1:
        parser.error("--workers must be at least 1")
    return args


def main() -> None:
    args = parse_args()
    targets = TARGETS if args.target == "all" else (args.target,)
    for target in targets:
        run_target(target, args.workers)


if __name__ == "__main__":
    main()
