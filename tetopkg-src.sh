#!/bin/bash
# Usage: ./tetopkg-src.sh <pkgname>
set -euo pipefail

PKG="$1"
TEMPLATE="srcpkgs/${PKG}/template"

[ -f "$TEMPLATE" ] || { echo "Template tidak ditemukan: $TEMPLATE"; exit 1; }

source "$TEMPLATE"

WORKDIR="build/${pkgname}-${version}"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR/buildroot"
cd "$WORKDIR"

echo ":: Downloading distfile..."
curl -L -o installer.exe "$distfiles"

echo ":: Extracting installer..."
7z x installer.exe -obuildroot/

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

[deps]
depends = []
EOF

echo ":: Packing .tetopkg..."
../../teto-pack --tetobuild TETOBUILD --prefix buildroot \
    --output "${pkgname}-${version}-${revision}-${arch}.tetopkg"

echo ":: Done: ${WORKDIR}/${pkgname}-${version}-${revision}-${arch}.tetopkg"