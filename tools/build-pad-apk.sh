#!/usr/bin/env bash
# 从公开 Java 源码 + 官方 APK 里的引擎二进制，打包一个可安装的 pad 变体。
#
# 这不是「从引擎源码构建」：引擎 .so 与 assets 来自官方发行版 APK（用户自备，
# 本仓库不分发），本仓库只提供 Java/资源层的改动。详见 README-PAD.md。
#
# 用法：
#   bash tools/extract-official-apk.sh /path/to/app.spektralab.apk
#   bash tools/build-pad-apk.sh
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC=$ROOT/app/src/main
STAGE=${STAGE:-$ROOT/.pad-build}
WORK=$STAGE/work
OUT=$STAGE/SpektraLab-pad.apk
PKG_ID=${PKG_ID:-app.spektralab.pad}
VERSION=${VERSION:-1.6.0t-pad.1}

: "${ANDROID_HOME:?需要设置 ANDROID_HOME（Android SDK 路径）}"
AJ=$ANDROID_HOME/platforms/android-36/android.jar
[ -f "$AJ" ] || { echo "缺少 $AJ（需要 SDK Platform 36）" >&2; exit 1; }

[ -d "$STAGE/assets" ] || { echo "缺少 $STAGE/assets，先运行 tools/extract-official-apk.sh" >&2; exit 1; }
[ -d "$STAGE/lib/arm64-v8a" ] || { echo "缺少 $STAGE/lib/arm64-v8a" >&2; exit 1; }

SIGN=${SIGN:-$HOME/.local/share/spektralab-pad}
mkdir -p "$SIGN"; chmod 700 "$SIGN"
if [ ! -f "$SIGN/signing-pass" ]; then
    (umask 077; python3 -c 'import secrets; print(secrets.token_hex(24))' > "$SIGN/signing-pass")
fi
if [ ! -f "$SIGN/pad.keystore" ]; then
    keytool -genkeypair -keystore "$SIGN/pad.keystore" -storetype PKCS12 \
        -storepass:file "$SIGN/signing-pass" -keypass:file "$SIGN/signing-pass" \
        -alias spektralab-pad -keyalg RSA -keysize 2048 -validity 3650 \
        -dname 'CN=SpektraLab Pad (local build)' >/dev/null 2>&1
    chmod 600 "$SIGN/pad.keystore"
fi

rm -rf "$WORK"
mkdir -p "$WORK/classes" "$WORK/dex" "$WORK/gen"

# 1) 并存版 Manifest：只改包名、Activity 全名与版本名，其余保持上游。
sed -e "s/package=\"app\.spektralab\"/package=\"$PKG_ID\"/" \
    -e 's/android:name="\.MainActivity"/android:name="app.spektralab.MainActivity"/' \
    -e "s/android:versionName=\"[^\"]*\"/android:versionName=\"$VERSION\"/" \
    "$SRC/AndroidManifest.xml" > "$WORK/AndroidManifest.xml"

# 2) 资源 + assets
aapt package -f -M "$WORK/AndroidManifest.xml" -S "$SRC/res" -A "$STAGE/assets" \
     -I "$AJ" -J "$WORK/gen" --custom-package app.spektralab -F "$WORK/res.apk"

# 3) Java -> DEX。注意不要让管道吞掉 javac 的失败码。
mapfile -t JAVA < <(find "$SRC/java" "$WORK/gen" -name '*.java')
echo "javac: ${#JAVA[@]} 个源文件"
if ! javac -source 17 -target 17 -encoding UTF-8 -classpath "$AJ" \
      -d "$WORK/classes" "${JAVA[@]}" > "$WORK/javac.log" 2>&1; then
    echo "JAVAC_FAILED" >&2; tail -30 "$WORK/javac.log" >&2; exit 1
fi
mapfile -t CLS < <(find "$WORK/classes" -name '*.class')
d8 --release --min-api 24 --lib "$AJ" --output "$WORK/dex" "${CLS[@]}"

# 4) 合并 res + classes.dex + 官方 native 库
python3 - "$WORK" "$STAGE" <<'PY'
import sys, zipfile
from pathlib import Path
work, stage = Path(sys.argv[1]), Path(sys.argv[2])
with zipfile.ZipFile(work / 'res.apk') as src, \
     zipfile.ZipFile(work / 'unsigned.apk', 'w', zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        dst.writestr(info, src.read(info.filename))
    dst.write(work / 'dex' / 'classes.dex', 'classes.dex')
    for so in sorted((stage / 'lib' / 'arm64-v8a').glob('*.so')):
        dst.write(so, f'lib/arm64-v8a/{so.name}')
PY

# 5) 对齐 + 签名 + 校验
zipalign -f -P 16 4 "$WORK/unsigned.apk" "$WORK/aligned.apk"
apksigner sign --ks "$SIGN/pad.keystore" --ks-key-alias spektralab-pad \
    --ks-pass "file:$SIGN/signing-pass" --out "$OUT" "$WORK/aligned.apk"
apksigner verify --verbose "$OUT" | head -6
zipalign -c -P 16 4 "$OUT"
aapt dump badging "$OUT" | grep -E '^package:|sdkVersion|targetSdkVersion|native-code|application-label:'
ls -l "$OUT"
echo "BUILD_PAD_PASS"
