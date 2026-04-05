#!/usr/bin/env python3
"""
manifest.json 자동 생성 스크립트
GitHub Actions에서 실행됩니다.

추적 대상 폴더: mods, config, resourcepacks, shaderpacks
"""

import json
import hashlib
import os
from datetime import datetime, timezone

# ─── 설정 ────────────────────────────────────────────────
TRACKED_DIRS = ['mods', 'config', 'resourcepacks', 'shaderpacks']
MANIFEST_FILE = 'manifest.json'
BRANCH = os.environ.get('GITHUB_REF_NAME', 'main')
REPO = os.environ.get('GITHUB_REPOSITORY', 'YOUR_USERNAME/YOUR_REPO')
# ──────────────────────────────────────────────────────────


def md5_of_file(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def scan_files() -> list:
    files = []
    for dir_name in TRACKED_DIRS:
        if not os.path.isdir(dir_name):
            continue
        for root, _, filenames in os.walk(dir_name):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                full_path = os.path.join(root, filename)
                rel_path = full_path.replace('\\', '/')
                url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{rel_path}"
                files.append({
                    "path": rel_path,
                    "url": url,
                    "md5": md5_of_file(full_path),
                    "size": os.path.getsize(full_path)
                })
    return files


def bump_version(current_version: str) -> str:
    """버전 마지막 숫자를 1 증가시킵니다. (예: 1.0.3 → 1.0.4)"""
    parts = current_version.split('.')
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except (ValueError, IndexError):
        parts = ['1', '0', '0']
    return '.'.join(parts)


def main():
    new_files = scan_files()

    # 기존 manifest 읽기
    old_manifest = None
    if os.path.isfile(MANIFEST_FILE):
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            try:
                old_manifest = json.load(f)
            except json.JSONDecodeError:
                pass

    # 버전 결정
    if old_manifest:
        old_file_map = {f['path']: f['md5'] for f in old_manifest.get('files', [])}
        new_file_map = {f['path']: f['md5'] for f in new_files}
        if old_file_map != new_file_map:
            version = bump_version(old_manifest.get('version', '1.0.0'))
            print(f"변경 감지됨: {old_manifest['version']} → {version}")
        else:
            version = old_manifest['version']
            print(f"변경 없음: {version} 유지")
    else:
        version = '1.0.0'
        print(f"신규 manifest 생성: {version}")

    manifest = {
        "version": version,
        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "repository": f"https://github.com/{REPO}",
        "files": new_files
    }

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"manifest.json 생성 완료 — {len(new_files)}개 파일, 버전 {version}")


if __name__ == '__main__':
    main()
