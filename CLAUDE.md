# CLAUDE.md

Guidance for Claude Code sessions working in this repo.

## What this is

`orac-apt` is the **public**, signed APT repository for ORAC's OS-level packages. Every push to `main` runs
`.github/workflows/publish.yml`, which tests, builds every `packages/*/build.sh`, signs the repo and deploys it
to <https://rick-masterson.github.io/orac-apt/>.

ORAC itself (the reasoning node) lives in the **private** repo `rick-masterson/orac-workspace`
(`~/Workspaces/orac-workspace`). Never copy its code, notes, vault or persona into this public repo without
asking.

## Decision: remix, not distro (2026-09-24)

The machine runs **Shadowfetch Linux 5.0.1 "Umbra"** (the tty banner `/etc/issue` still said 4.1.0 until 2026-10-10), a Debian-testing-based KDE Plasma 6 distro. The user
wanted their own update channel on GitHub, but doesn't have the capacity to maintain a full distro. So this
repo is an **add-on repo layered on Shadowfetch**:
- Shadowfetch keeps supplying the base system and its own updates (`/etc/apt/sources.list.d/shadowfetch.sources`).
- This repo only adds `orac-*` packages, installed through the same `apt` and Shadowfetch's Fireproof updates.

Don't propose a full fork unless asked.

Shadowfetch licences, checked from `/usr/share/doc/shadowfetch-*/copyright`: MIT for most packages,
GPL-3 for `shadowfetch-fireline` and `shadowfetch-drkonqi-pickup`, LGPL-2.1+ for `shadowfetch-themes`.
There are no public source repos, only the website and the APT repo. No Shadowfetch files or marks ship here.

## Where Shadowfetch keeps things (verified on this machine)

- Branding: `shadowfetch-branding` holds the Plymouth theme `shadowfetch`, wallpapers and `/usr/share/shadowfetch/*`.
  `shadowfetch-themes` holds the Plasma look-and-feel `org.shadowfetch.{dark,ice}`, the colour schemes, Konsole
  schemes and the SDDM theme `umbra`.
- Boot splash: selected in `/etc/plymouth/plymouthd.conf` (`Theme=`), **not** through the `default.plymouth`
  alternative. Switch with `sudo plymouth-set-default-theme -R <name>` (it lives in `/usr/sbin`).
- Terminal banner: `/etc/profile.d/shadowfetch.sh` (from `shadowfetch-defaults`) runs `fastfetch` once per
  session; the per-user `~/.config/fastfetch/config.jsonc` picks the logo.
- Login message: `/etc/motd` is an **untracked** copy of `/usr/share/shadowfetch/motd`, and nothing rewrites it.
  `/etc/issue` belongs to `base-files` (a conffile): leave it alone.
- Agent provider system (not used here, but it was the other reading of the first request): declarative
  manifests in `/usr/share/shadowfetch/providers/`, the `approved.json` policy with sha256 pins, and the registry
  in `/usr/lib/shadowfetch/missions/sf_providers.py`.

## orac-branding (current: 1.3.1-1)

`packages/orac-branding/`: `root/` is the filesystem tree, `DEBIAN/` holds control and the maintainer scripts,
`build.sh` uses plain `dpkg-deb`. It ships:
- Plymouth theme `orac`. The script was rewritten against the real script-plugin API: the original zip used
  `Sprite.SetScale` and `Plymouth.GetTime` (neither exists), and its password sprites were function locals that
  vanish. **Correction (2026-09-25):** the 1.0.0 changelog also calls `Plymouth.SetMessageFunction` nonexistent.
  It is a valid alias of `SetDisplayMessageFunction` (Plymouth's `script-lib-plymouth.script`). Recorded in
  1.3.0's changelog entry. To check any Plymouth theme, use the `plymouth-theme` skill's checker in
  `rick-masterson/Claude` (`plugins/desktop-theming`), which reads its API lists from Plymouth's source.
- Plasma look-and-feel `org.orac.workstation` with a KSplash, on `ShadowfetchDark` plus a purple accent. The
  original QML's bare `letterSpacing` made it fail to load.
- Wallpapers: `OracOrb`, `OracMinimal`, `OracWorkstation`.
- Terminal banner: `/usr/share/orac/fastfetch/`, plus `orac-terminal-theme apply|revert|status` (per user,
  backs up to `config.jsonc.pre-orac`).
- Konsole: the `OracVoid` scheme and an `ORAC` profile, selectable but not the default.
- Login message: `/etc/motd` becomes a link to `/usr/share/orac/motd`. This happens only while it is the stock
  copy; the original is backed up to `/etc/motd.pre-orac` and restored by `postrm`, and a hand-edited motd is
  left alone.
- Maintainer scripts honour `DPKG_ROOT`, and the tests run them against a scratch root.
- Boot to desktop (1.3.0): `orac-boot-theme apply|revert|status` (`/usr/sbin`, root) switches GRUB, Plymouth and
  SDDM together. GRUB and SDDM use drop-ins `/etc/default/grub.d/99-orac.cfg` and `/etc/sddm.conf.d/99-orac.conf`,
  which load after Shadowfetch's `10-shadowfetch` ones, so Shadowfetch updates don't undo them. The Plymouth theme
  in use before is kept in `/var/lib/orac-branding/plymouth.previous`. `prerm` reverts before removal.
- GRUB theme `orac` (`/usr/share/grub/themes/orac`): fonts are pf2 files built with `grub-mkfont -n <family>`.
  GRUB names a font `<family> <style> <size>`, so `-n` must be the family only; `TestGrubTheme` checks that every
  font in `theme.txt` matches a name embedded in a shipped pf2.
- SDDM theme `orac` (Qt 6): the ORAC core video (`orac-core.webm`, from the ORAC web console) behind a glass
  panel. Preview it without logging out: `sddm-greeter-qt6 --test-mode --theme <dir>` (`sddm --version` hangs).
- Cursor theme `Orac` (`/usr/share/icons/Orac`): Breeze cursors recoloured, SVG plus Xcursor. Rebuild with
  `python3 -I packages/orac-branding/tools/build_cursors.py packages/orac-branding/root/usr/share/icons/Orac`.
  This machine's libXcursor searches `~/.icons:/usr/share/icons:/usr/share/pixmaps`, not `~/.local/share/icons`.
- Plasma style `orac` (Breeze Dark with Orac colours; panel and widgets only) and the animated wallpaper plugin
  `org.orac.living` (QML layers, no compiled shaders: this machine has no `qsb`).

Machines: the notes above were first written on the workstation. On **orac-D1** (192.168.1.203, checked
2026-10-10) 1.2.1-1 was installed but the ORAC splash had never been activated: `plymouthd.conf` still said
`Theme=shadowfetch` (last changed 2026-09-10, before this repo existed). GRUB used Shadowfetch's `umbra` theme and
SDDM its `umbra` login theme until `orac-boot-theme apply`.

## Open items

- **Boot splash is "a little glitchy"** (user report, cause not yet described). Ask what it looked like:
  flicker, dot stutter, bar jumps, or a handoff jump at SDDM. Ship the fix as 1.2.1.
- Duplicate Claude Desktop apt source: the user should `sudo rm /etc/apt/sources.list.d/claude-desktop.sources`
  (the `.list` is package-managed and gets recreated).
- ORAC itself as a `.deb` here: not started.

## Rules

- **Ship an update:** change the package, bump `Version:` in `DEBIAN/control`, add an entry to `changelog`,
  run the tests, push. apt only upgrades when the version increases.
- **Tests:** `python3 -m unittest discover -s tests`. The QML test skips without PyQt6; it is installed on
  this machine.
- **Pushing:** plain `git push` fails ("Repository not found"). Use
  `git -c credential.helper= -c "credential.helper=!gh auth git-credential" push`.
- **Signing:** ed25519 key `5E0EE21BEFCDAE36233DAE59DFEB354008E686D7`, expires 2029-09-24. It is in the
  `APT_SIGNING_KEY` Actions secret, with a backup in `~/.gnupg`. Never commit a private key.
- **Anything needing `sudo`:** give the user the command. They run it themselves.
- Stage explicit paths (`git add <path>`), never `git add -A`.
