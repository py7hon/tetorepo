#!/bin/bash
# Usage: ./tetopkg-src.sh <pkgname>
set -euo pipefail

PKG="$1"
TEMPLATE="srcpkgs/${PKG}/template"

[ -f "$TEMPLATE" ] || { echo "Template tidak ditemukan: $TEMPLATE"; exit 1; }

source <(sed 's/\r$//' "$TEMPLATE")

WORKDIR="build/${pkgname}-${version}"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR/buildroot"
cd "$WORKDIR"

echo ":: Downloading distfile..."
curl -fL -o payload.bin "$distfiles"

echo ":: Calculating SHA256 checksum..."
if command -v sha256sum >/dev/null 2>&1; then
    INSTALLER_SHA256="$(sha256sum payload.bin | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
    INSTALLER_SHA256="$(shasum -a 256 payload.bin | awk '{print $1}')"
else
    INSTALLER_SHA256="$(certutil -hashfile payload.bin SHA256 | sed -n '2p' | tr -d ' \r\n')"
fi

TYPE="${installer_type:-exe}"

if [ "$TYPE" = "zip" ]; then
    echo ":: Zip installer payload detected, extracting to buildroot..."
    if 7z x payload.bin -obuildroot >/dev/null 2>&1; then
        echo ":: Successfully extracted zip payload."
    else
        unzip -q payload.bin -d buildroot 2>/dev/null || true
    fi
fi

echo ":: Generating TETOBUILD..."
cat > TETOBUILD <<EOF
[meta]
pkgname = "${pkgname}"
pkgver = "${version}"
pkgrel = ${revision}
pkgdesc = "${short_desc}"
arch = ["${arch}"]
url = "${homepage}"
license = ["${license}"]
main_exe = "${main_exe:-}"
shortcut_name = "${shortcut_name:-${pkgname}}"
installer_type = "${TYPE}"
installer_url = "${distfiles}"
installer_sha256 = "${INSTALLER_SHA256}"
installer_args = "${installer_args:-}"

[deps]
depends = []
EOF

echo ":: Packing .tetopkg..."
../../teto-pack --tetobuild TETOBUILD --prefix buildroot \
    --output "${pkgname}-${version}-${revision}-${arch}.tetopkg"

echo ":: Done: ${WORKDIR}/${pkgname}-${version}-${revision}-${arch}.tetopkg"