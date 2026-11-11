#!/usr/bin/env bash
# 从你本机的官方 SpektraLab APK 里取出 assets 与 ARM64 引擎库，
# 供 tools/build-pad-apk.sh 重新打包。仓库不分发这些二进制。
#
# 用法：bash tools/extract-official-apk.sh /path/to/app.spektralab.apk
set -euo pipefail

APK=${1:?用法: $0 /path/to/official.apk}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
STAGE=${STAGE:-$ROOT/.pad-build}

[ -f "$APK" ] || { echo "找不到 $APK" >&2; exit 1; }
mkdir -p "$STAGE"

python3 - "$APK" "$STAGE" <<'PY'
import sys, zipfile
from pathlib import Path
apk, stage = Path(sys.argv[1]), Path(sys.argv[2])
n = 0
with zipfile.ZipFile(apk) as z:
    for info in z.infolist():
        name = info.filename
        if name.startswith('assets/') or (name.startswith('lib/arm64-v8a/') and name.endswith('.so')):
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(name))
            n += 1
print(f'extracted {n} files to {stage}')
PY

du -sh "$STAGE/assets" "$STAGE/lib/arm64-v8a" 2>/dev/null || true
echo "EXTRACT_OK"
