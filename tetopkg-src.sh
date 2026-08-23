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
curl -fL -o installer.exe "$distfiles"

echo ":: Extracting installer..."
if 7z x installer.exe -obuildroot >/dev/null 2>&1; then
    echo ":: Successfully extracted with 7z."
    rm -rf buildroot/\$* 2>/dev/null || true
else
    echo ":: 7z extraction skipped/failed. Running installer silently..."
    chmod +x installer.exe

    BUILDROOT_ABS="$(pwd)/buildroot"
    if command -v wslpath >/dev/null 2>&1; then
        BUILDROOT_WIN="$(wslpath -w "$BUILDROOT_ABS")"
    elif command -v cygpath >/dev/null 2>&1; then
        BUILDROOT_WIN="$(cygpath -w "$BUILDROOT_ABS")"
    else
        BUILDROOT_WIN="Z:${BUILDROOT_ABS//\//\\}"
    fi

    TYPE="${installer_type:-inno}"
    if [ -n "${installer_args:-}" ]; then
        INSTALL_FLAGS="$installer_args"
    elif [ "$TYPE" = "nsis" ]; then
        INSTALL_FLAGS="/S /D=${BUILDROOT_WIN}"
    else
        INSTALL_FLAGS="/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /DIR=${BUILDROOT_WIN}"
    fi

    echo ":: Executing installer with flags: $INSTALL_FLAGS"
    if command -v wine >/dev/null 2>&1; then
        wine ./installer.exe $INSTALL_FLAGS
    elif [[ "${OSTYPE:-}" == "msys" || "${OSTYPE:-}" == "cygwin" || "${OSTYPE:-}" == "win32" || "$(uname -s 2>/dev/null)" == MINGW* || "$(uname -s 2>/dev/null)" == MSYS* ]]; then
        ./installer.exe $INSTALL_FLAGS
    else
        echo "Error: Cannot execute Windows binary on Linux without Wine."
        exit 1
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

[deps]
depends = []
EOF

echo ":: Packing .tetopkg..."
../../teto-pack --tetobuild TETOBUILD --prefix buildroot \
    --output "${pkgname}-${version}-${revision}-${arch}.tetopkg"

echo ":: Done: ${WORKDIR}/${pkgname}-${version}-${revision}-${arch}.tetopkg"