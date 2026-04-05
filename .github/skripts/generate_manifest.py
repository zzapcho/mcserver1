#!/usr/bin/env python3
import json, hashlib, os
from datetime import datetime, timezone

TRACKED_DIRS  = ['mods', 'config', 'resourcepacks', 'shaderpacks']
MANIFEST_FILE = 'manifest.json'
BRANCH        = os.environ.get('GITHUB_REF_NAME', 'main')
REPO          = os.environ.get('GITHUB_REPOSITORY', 'zzapcho/mcserver1')

def md5_of_file(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def scan_files():
    files = []
    for d in TRACKED_DIRS:
        if not os.path.isdir(d): continue
        for root, _, filenames in os.walk(d):
            for filename in filenames:
                if filename.startswith('.'): continue
                full = os.path.join(root, filename)
                rel  = full.replace('\\', '/')
                files.append({
                    "path": rel,
                    "url":  f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{rel}",
                    "md5":  md5_of_file(full),
                    "size": os.path.getsize(full)
                })
    return files

def bump(version):
    parts = version.split('.')
    try: parts[-1] = str(int(parts[-1]) + 1)
    except: parts = ['1', '0', '0']
    return '.'.join(parts)

def main():
    new_files = scan_files()

    old = {}
    if os.path.isfile(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
                old = json.load(f)
        except: pass

    old_map = {f['path']: f['md5'] for f in old.get('files', [])}
    new_map = {f['path']: f['md5'] for f in new_files}
    version = bump(old.get('version', '1.0.0')) if old_map != new_map else old.get('version', '1.0.0')

    # ★ 기존 필드(gameVersion, modLoader, servers 등) 유지하고 덮어쓰기
    manifest = {
        **old,
        "version":    version,
        "timestamp":  datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "repository": f"https://github.com/{REPO}",
        "files":      new_files
    }

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"완료 — {len(new_files)}개 파일, 버전 {version}")

if __name__ == '__main__':
    main()
