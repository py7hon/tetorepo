#!/usr/bin/env python3
"""
build-winget-index.py — Parse winget-pkgs YAML manifests and generate compact index.toml & package TOMLs.
"""
import sys
import os
import glob
import re
import argparse
import sys
import yaml
import tomli_w

try:
    from packaging.version import parse as parse_version
except ImportError:
    def parse_version(ver_str: str):
        """Fallback version parser extracting numeric tuple components."""
        nums = [int(n) for n in re.findall(r'\d+', str(ver_str))]
        if nums:
            return tuple(nums)
        return (str(ver_str),)

def get_highest_version(version_dirs):
    """Sort version directory names and return the highest version string."""
    sorted_dirs = sorted(
        version_dirs,
        key=lambda v: parse_version(v.strip().lstrip('v'))
    )
    return sorted_dirs[-1]

def extract_installer_info(installer_yaml_path):
    """
    Extract x64 installer information from *.installer.yaml.
    Returns dict with keys: installer_type, installer_url, installer_sha256, silent_switch, product_code, installer_flavor.
    Raises ValueError if no x64 installer variant is found.
    """
    with open(installer_yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Invalid installer YAML format (not a dict)")

    root_type = data.get('InstallerType', '')
    root_url = data.get('InstallerUrl', '')
    root_sha = data.get('InstallerSha256', '')
    root_switches = data.get('InstallerSwitches', {}) or {}
    root_product_code = data.get('ProductCode', '')

    installers = data.get('Installers', [])
    if not isinstance(installers, list) or len(installers) == 0:
        # If no Installers array, check if root has info and architecture
        root_arch = str(data.get('Architecture', '')).lower()
        if root_arch in ('x64', 'amd64'):
            selected_installer = {}
        else:
            raise ValueError("No installers array and root architecture is not x64")
    else:
        # Search for x64 installer
        selected_installer = None
        for inst in installers:
            if not isinstance(inst, dict):
                continue
            arch = str(inst.get('Architecture', '')).lower()
            if arch in ('x64', 'amd64'):
                selected_installer = inst
                break

        if selected_installer is None:
            raise ValueError("No x64 installer variant found")

    installer_type = str(selected_installer.get('InstallerType', root_type) or root_type or '').lower()
    installer_url = str(selected_installer.get('InstallerUrl', root_url) or root_url or '')
    installer_sha256 = str(selected_installer.get('InstallerSha256', root_sha) or root_sha or '')
    product_code = str(selected_installer.get('ProductCode', root_product_code) or root_product_code or '')

    # Switches
    switches = selected_installer.get('InstallerSwitches', {}) or root_switches
    if not isinstance(switches, dict):
        switches = {}

    silent_switch = switches.get('Silent', '') or switches.get('SilentWithProgress', '') or ''
    installer_flavor = switches.get('Custom', '') or ''

    if not installer_url:
        raise ValueError("InstallerUrl is empty")

    return {
        "installer_type": installer_type,
        "installer_url": installer_url,
        "installer_sha256": installer_sha256,
        "silent_switch": silent_switch,
        "product_code": product_code,
        "installer_flavor": installer_flavor,
    }

def extract_locale_info(ver_dir, publisher, app_name):
    """
    Extract package metadata from *.locale.en-US.yaml or fallback locale files.
    """
    en_us_path = os.path.join(ver_dir, f"{publisher}.{app_name}.locale.en-US.yaml")
    target_path = None

    if os.path.exists(en_us_path):
        target_path = en_us_path
    else:
        # Fallback to any locale file
        candidates = glob.glob(os.path.join(ver_dir, f"{publisher}.{app_name}.locale.*.yaml"))
        if candidates:
            target_path = candidates[0]
        else:
            # Fallback to default version yaml file
            fallback_yaml = os.path.join(ver_dir, f"{publisher}.{app_name}.yaml")
            if os.path.exists(fallback_yaml):
                target_path = fallback_yaml

    if not target_path or not os.path.exists(target_path):
        raise ValueError("No locale or version metadata YAML file found")

    with open(target_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Invalid locale YAML format")

    pkg_name = data.get('PackageName', app_name) or app_name
    short_desc = data.get('ShortDescription', '') or data.get('Description', '') or ''
    pub = data.get('Publisher', publisher) or publisher
    pkg_url = data.get('PackageUrl', '') or ''
    license_str = data.get('License', '') or ''

    return {
        "package_name": pkg_name,
        "short_description": short_desc,
        "publisher": pub,
        "package_url": pkg_url,
        "license": license_str,
    }

def process_manifests(manifests_dir, output_dir):
    os.makedirs(os.path.join(output_dir, "packages"), exist_ok=True)

    packages_summary = []
    success_count = 0
    skipped_count = 0
    skip_reasons = {}

    def log_skip(pkg_id, reason):
        nonlocal skipped_count
        skipped_count += 1
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        sys.stderr.write(f"[WARN] Skipping {pkg_id}: {reason}\n")

    # Structure: manifests_dir/{c}/{Publisher}/{AppName}/{version}/
    if not os.path.exists(manifests_dir):
        print(f"[ERROR] Manifests directory '{manifests_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    for c in sorted(os.listdir(manifests_dir)):
        c_path = os.path.join(manifests_dir, c)
        if not os.path.isdir(c_path):
            continue

        for publisher in sorted(os.listdir(c_path)):
            pub_path = os.path.join(c_path, publisher)
            if not os.path.isdir(pub_path):
                continue

            for app_name in sorted(os.listdir(pub_path)):
                app_path = os.path.join(pub_path, app_name)
                if not os.path.isdir(app_path):
                    continue

                package_identifier = f"{publisher}.{app_name}"

                try:
                    version_dirs = [
                        v for v in os.listdir(app_path)
                        if os.path.isdir(os.path.join(app_path, v))
                    ]
                    if not version_dirs:
                        log_skip(package_identifier, "No version subdirectories found")
                        continue

                    highest_version = get_highest_version(version_dirs)
                    ver_dir = os.path.join(app_path, highest_version)

                    # Look for installer yaml file
                    installer_yaml_path = os.path.join(ver_dir, f"{publisher}.{app_name}.installer.yaml")
                    if not os.path.exists(installer_yaml_path):
                        log_skip(package_identifier, f"Missing installer YAML file at {installer_yaml_path}")
                        continue

                    installer_info = extract_installer_info(installer_yaml_path)
                    locale_info = extract_locale_info(ver_dir, publisher, app_name)

                    # Write individual package TOML
                    pkg_toml_data = {
                        "package_identifier": package_identifier,
                        "package_name": locale_info["package_name"],
                        "publisher": locale_info["publisher"],
                        "version": highest_version,
                        "installer_type": installer_info["installer_type"],
                        "installer_url": installer_info["installer_url"],
                        "installer_sha256": installer_info["installer_sha256"],
                        "installer_flavor": installer_info["installer_flavor"],
                        "silent_switch": installer_info["silent_switch"],
                        "product_code": installer_info["product_code"],
                        "pkgdesc": locale_info["short_description"],
                        "url": locale_info["package_url"],
                        "license": locale_info["license"],
                    }

                    pkg_toml_path = os.path.join(output_dir, "packages", f"{package_identifier}.toml")
                    with open(pkg_toml_path, "wb") as f:
                        tomli_w.dump(pkg_toml_data, f)

                    packages_summary.append({
                        "package_identifier": package_identifier,
                        "package_name": locale_info["package_name"],
                        "publisher": locale_info["publisher"],
                        "short_description": locale_info["short_description"],
                        "latest_version": highest_version,
                    })

                    success_count += 1

                except Exception as e:
                    log_skip(package_identifier, str(e))

    # Write summary index.toml
    index_data = {
        "meta": {
            "name": "winget-mirror",
            "description": "Mirrored index of winget-pkgs manifests",
            "total_packages": success_count,
        },
        "packages": packages_summary,
    }

    index_toml_path = os.path.join(output_dir, "index.toml")
    with open(index_toml_path, "wb") as f:
        tomli_w.dump(index_data, f)

    print(f"\n:: Winget Index Build Complete ::")
    print(f"Successfully indexed : {success_count} packages")
    print(f"Skipped              : {skipped_count} packages")
    if skip_reasons:
        print("Skip Breakdown:")
        for reason, count in skip_reasons.items():
            print(f"  - {reason}: {count}")

def main():
    parser = argparse.ArgumentParser(
        description="Build compact index.toml and detail TOMLs from winget-pkgs manifests."
    )
    parser.add_argument("manifests_dir", help="Path to winget-pkgs manifests directory")
    parser.add_argument("output_dir", help="Path to output winget-index directory")

    args = parser.parse_args()
    process_manifests(args.manifests_dir, args.output_dir)

if __name__ == "__main__":
    main()
