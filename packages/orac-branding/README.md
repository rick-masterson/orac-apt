# orac-branding

ORAC's look for this Shadowfetch machine, shipped as a Debian package laid out the same way as
`shadowfetch-branding` and `shadowfetch-themes`. It sits on top of Shadowfetch and replaces nothing:
the colour scheme is still `ShadowfetchDark`, with a purple accent.

| Path | What |
|---|---|
| `/usr/share/plymouth/themes/orac/` | Boot splash showing real boot progress, boot messages and the encrypted-drive unlock prompt |
| `/usr/share/plasma/look-and-feel/org.orac.workstation/` | Global theme, including the KSplash login splash |
| `/usr/share/wallpapers/Orac{Orb,Minimal,Workstation}/` | Wallpaper sets, one image per resolution |
| `/usr/share/orac/fastfetch/`, `/usr/bin/orac-terminal-theme` | ORAC terminal banner; `orac-terminal-theme apply` / `revert` per user |
| `/usr/share/konsole/OracVoid.colorscheme`, `ORAC.profile` | Konsole colours and profile (selectable, not default) |
| `/usr/share/orac/motd` → `/etc/motd` | Console/SSH login message; Shadowfetch's is kept as `/etc/motd.pre-orac` and restored on removal |

## Build

```bash
packages/orac-branding/build.sh
```
The build needs only `dpkg-deb`. It writes `dist/orac-branding_<version>_all.deb`, and `dist/` is gitignored.

## Install and activate

```bash
sudo apt install ./dist/orac-branding_1.0.0-1_all.deb
```
Installing registers the boot splash but leaves it switched off. To switch to it (this also
rebuilds the initramfs):
```bash
sudo plymouth-set-default-theme -R orac
```
To use the global theme, go to System Settings → Colors & Themes → Global Theme → **ORAC Workstation**.
To use just the login splash, go to Splash Screen → **ORAC Workstation**.

## Test the boot splash without rebooting

```bash
sudo plymouthd --debug --debug-file=/tmp/plymouth.log && sudo plymouth --show-splash
```
```bash
for i in $(seq 0 100); do sudo plymouth system-update --progress=$i; sleep 0.03; done
```
(At real boot the bar is driven by plymouthd's own boot-progress estimate; `system-update` feeds the
same bar, which is also how an offline update's progress shows.)
```bash
sudo plymouth display-message --text="ORAC CORE ONLINE"; sleep 3; sudo plymouth --quit
```
If anything fails, `/tmp/plymouth.log` shows script errors.

## Revert

```bash
sudo plymouth-set-default-theme -R shadowfetch
```

## Provenance

Built from `orac-plymouth-DEBIAN-WORKING.zip` and `orac-workstation-theme.zip`. The changes from
those zips are listed in `changelog`. `tests/test_branding.py` (repo root) pins them.
