# tetorepo

Official package template repository for `tetopkg`.

## Package Template Specification

Package recipes in `srcpkgs/<pkgname>/template` define how software packages are built and packaged into `.tetopkg` format.

### Installer Flavor & Silent Flags

`installer_flavor` specifies raw command-line flags directly for silent installation.
Packagers specify the exact CLI flags required by the application's installer type.

#### Reference Flag Guide for Common Installers:
- **Inno Setup**: `/SILENT` or `/VERYSILENT /SP- /NORESTART` or `/AUTO /SILENT`
- **NSIS (Nullsoft)**: `/S` or `/S /D=C:\Path\To\Install`
- **MSI (Windows Installer)**: `/qn` or `/qb REBOOT=ReallySuppress`
- **InstallShield**: `/s /sms`
- **SetupX / Microsoft Generic**: `/q /norestart`

### Standard Template Reference Example (AIMP Audio Player)

```sh
pkgname=aimp
version=5.40.2722
revision=1
short_desc="AIMP audio player"
maintainer="Iqbal Rifai <yukifag@proton.me>"
license="Freeware"
homepage="https://www.aimp.ru"
distfiles="https://aimp.ru/files/desktop/builds/aimp_${version}_w64.exe"
installer_type="exe"
installer_flavor="/AUTO /SILENT"
arch="x86_64"
main_exe="AIMP.exe"
```

## Winget Mirror Workflow

`tetorepo` contains an automated GitHub Action workflow `.github/workflows/mirror-winget.yml` that mirrors manifests from `microsoft/winget-pkgs` to Cloudflare R2 storage.

### Workflow Details
- **Script**: `build-winget-index.py`
- **Schedule**: Every day at 03:00 UTC (`cron: "0 3 * * *"`) and manually via `workflow_dispatch`.
- **Outputs**:
  - `s3://${R2_BUCKET}/winget-mirror/index.toml` — Compact index of all mirrored packages.
  - `s3://${R2_BUCKET}/winget-mirror/packages/<PackageIdentifier>.toml` — Detailed manifest for each package.

### Client Consumption (`tetopkg-cli`)
`tetopkg` client applications consume the mirrored index via public CDN endpoints:
- `https://<cdn-domain>/winget-mirror/index.toml`
- `https://<cdn-domain>/winget-mirror/packages/<PackageIdentifier>.toml`

This structure allows `tetopkg -Sw` and `tetopkg -Ssw` commands to query winget packages quickly with local caching without making direct calls to GitHub APIs.

