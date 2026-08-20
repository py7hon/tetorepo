#!/usr/bin/env python3
"""
gen-index.py — Generate index.toml dari kumpulan file .tetopkg di suatu folder.
Format mengikuti struct RepoIndex/RepoMeta/RepoPackage di crates/teto-repo-common/src/index.rs
"""
import sys
import os
import glob
import hashlib
import subprocess
import time
import tomllib  # python 3.11+
import tomli_w  # pip install tomli_w

def read_pkginfo(tetopkg_path: str) -> dict:
    """Extract .PKGINFO.toml dari dalam arsip .tetopkg (tar + zstd)."""
    # decompress zstd -> tar stream, lalu ambil file .PKGINFO.toml
    result = subprocess.run(
        f"zstd -dc '{tetopkg_path}' | tar -xO --wildcards '.PKGINFO.toml'",
        shell=True, capture_output=True, check=True
    )
    return tomllib.loads(result.stdout.decode("utf-8"))

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) != 5:
        print("Usage: gen-index.py <repo_dir> <output_index_toml> <repo_name> <repo_desc>")
        sys.exit(1)

    repo_dir, output_path, repo_name, repo_desc = sys.argv[1:5]

    packages = []
    for pkg_path in sorted(glob.glob(os.path.join(repo_dir, "*.tetopkg"))):
        print(f":: Reading {pkg_path}")
        info = read_pkginfo(pkg_path)
        pkg = info["package"]
        deps = info.get("deps", {})

        packages.append({
            "package": {
                "name": pkg["name"],
                "version": pkg["version"],
                "pkgrel": pkg.get("pkgrel", 1),
                "arch": pkg["arch"],
                "desc": pkg["desc"],
                "url": pkg["url"],
                "license": pkg["license"],
                "size": pkg.get("size", 0),
                "builddate": pkg.get("builddate", int(time.time())),
                "packager": pkg.get("packager", "gen-index"),
            },
            "deps": {
                "requires": deps.get("requires", []),
                "optional": deps.get("optional", []),
                "conflicts": deps.get("conflicts", []),
                "provides": deps.get("provides", []),
            },
        })

    index = {
        "meta": {
            "name": repo_name,
            "description": repo_desc,
            "url": "",
            "generated": int(time.time()),
        },
        "packages": packages,
    }

    with open(output_path, "wb") as f:
        tomli_w.dump(index, f)

    print(f":: Wrote {output_path} ({len(packages)} packages)")

if __name__ == "__main__":
    main()