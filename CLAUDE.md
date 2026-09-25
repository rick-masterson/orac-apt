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

The machine runs **Shadowfetch Linux 4.1.0 "Umbra"**, a Debian-testing-based KDE Plasma 6 distro. The user
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

## orac-branding (current: 1.2.0-1, installed on this machine)

`packages/orac-branding/`: `root/` is the filesystem tree, `DEBIAN/` holds control and the maintainer scripts,
`build.sh` uses plain `dpkg-deb`. It ships:
- Plymouth theme `orac`. The script was rewritten against the real script-plugin API: the original zip used
  `Sprite.SetScale` and `Plymouth.GetTime` (neither exists), and its password sprites were function locals that
  vanish. **Correction (2026-09-25):** the 1.0.0 changelog also calls `Plymouth.SetMessageFunction` nonexistent.
  It is a valid alias of `SetDisplayMessageFunction` (Plymouth's `script-lib-plymouth.script`). Say so in the next
  release's changelog entry. To check any Plymouth theme, use the `plymouth-theme` skill's checker in
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

State on this machine: 1.2.0-1 is installed from this repo, `Theme=orac`, the motd link is in place and the
ORAC banner is applied.

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
