# orac-apt

Signed APT repository for the ORAC spinoff packages, layered on Shadowfetch Linux (Debian). Every push to
`main` runs the tests, builds every package under `packages/`, signs the repository in GitHub Actions and
publishes it to <https://rick-masterson.github.io/orac-apt/>.

This is a remix, not a distro. Shadowfetch keeps supplying the base system and its own updates; this repo
only adds ORAC packages, delivered through the same `apt` and Fireproof updates.

## Use it on a machine

```bash
sudo curl -fsSLo /etc/apt/keyrings/orac-archive-keyring.gpg https://rick-masterson.github.io/orac-apt/orac-archive-keyring.gpg
```
Check the key before trusting it. The fingerprint must be `5E0E E21B EFCD AE36 233D  AE59 DFEB 3540 08E6 86D7`:
```bash
gpg --show-keys /etc/apt/keyrings/orac-archive-keyring.gpg
```
```bash
printf 'Types: deb\nURIs: https://rick-masterson.github.io/orac-apt/\nSuites: stable\nComponents: main\nSigned-By: /etc/apt/keyrings/orac-archive-keyring.gpg\n' | sudo tee /etc/apt/sources.list.d/orac.sources
```
```bash
sudo apt update && sudo apt install orac-branding
```

## Ship an update

1. Change the package under `packages/<name>/`.
2. Bump `Version:` in `packages/<name>/DEBIAN/control` and add an entry to `packages/<name>/changelog`.
   apt only upgrades when the version goes up.
3. Commit and push to `main`. When the `publish` workflow finishes, `sudo apt update && sudo apt upgrade`
   (or Fireproof) picks up the new version.

## Add a package

Create `packages/<name>/build.sh`. It takes the output directory as `$1` and writes one `.deb` into it;
`packages/orac-branding/build.sh` is the template. `scripts/build-repo.sh` picks up every
`packages/*/build.sh` automatically.

## Build locally

```bash
sh scripts/build-repo.sh
```
This writes an unsigned repository into `public/`, for checking layout only; apt refuses an unsigned repo.
Signing happens in CI from the `APT_SIGNING_KEY` Actions secret.

## Signing key

- ed25519, signing only, expires 2029-09-24. Fingerprint `5E0EE21BEFCDAE36233DAE59DFEB354008E686D7`.
- The private key exists in two places: the `APT_SIGNING_KEY` Actions secret, and the maintainer's `~/.gnupg`
  (the backup). It is never committed.
- A revocation certificate is in `~/.gnupg/openpgp-revocs.d/`.
- Before the key expires, extend it and publish the updated keyring:
  `gpg --quick-set-expire <fpr> 3y`, then update the secret.

## Licences

The ORAC artwork and theme files are GPL-3.0+ (see each package's `copyright`). The layout follows
Shadowfetch's own branding and themes packages; no Shadowfetch files or marks are shipped here.
