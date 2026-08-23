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
