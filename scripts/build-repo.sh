#!/bin/sh
# Build every package under packages/ and lay out a signed APT repository in $1 (default: public/).
#
#   APT_SIGNING_KEY   ASCII-armored private key (the GitHub Actions secret). Without it the
#                     repository is built UNSIGNED, which apt refuses -- only for local checks.
#
# Layout (what apt fetches):
#   dists/stable/{Release,InRelease,Release.gpg}
#   dists/stable/main/binary-{amd64,all}/Packages{,.gz}
#   pool/main/*.deb
#   orac-archive-keyring.gpg   public key for /etc/apt/keyrings
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
out=$(mkdir -p "${1:-$root/public}" && cd "${1:-$root/public}" && pwd)
suite=stable

rm -rf "$out/dists" "$out/pool"
mkdir -p "$out/pool/main"
for build in "$root"/packages/*/build.sh; do
    sh "$build" "$out/pool/main"
done

cd "$out"
for arch in amd64 all; do
    dir=dists/$suite/main/binary-$arch
    mkdir -p "$dir"
    apt-ftparchive packages pool/main > "$dir/Packages"
    gzip -9n -c "$dir/Packages" > "$dir/Packages.gz"
done

apt-ftparchive \
    -o APT::FTPArchive::Release::Origin=ORAC \
    -o APT::FTPArchive::Release::Label=ORAC \
    -o APT::FTPArchive::Release::Suite=$suite \
    -o APT::FTPArchive::Release::Codename=$suite \
    -o "APT::FTPArchive::Release::Architectures=amd64 all" \
    -o APT::FTPArchive::Release::Components=main \
    -o "APT::FTPArchive::Release::Description=ORAC packages for Shadowfetch" \
    release "dists/$suite" > "dists/$suite/Release"

if [ -z "${APT_SIGNING_KEY:-}" ]; then
    echo "build-repo: APT_SIGNING_KEY not set -- repository is UNSIGNED (local check only)" >&2
    exit 0
fi

GNUPGHOME=$(mktemp -d)
export GNUPGHOME
trap 'rm -rf "$GNUPGHOME"' EXIT
printf '%s\n' "$APT_SIGNING_KEY" | gpg --batch --quiet --import
fpr=$(gpg --batch --with-colons --list-secret-keys | awk -F: '/^fpr:/{print $10; exit}')
gpg --batch --yes --local-user "$fpr" --clearsign -o "dists/$suite/InRelease" "dists/$suite/Release"
gpg --batch --yes --local-user "$fpr" --armor --detach-sign -o "dists/$suite/Release.gpg" "dists/$suite/Release"
gpg --batch --yes --export "$fpr" > orac-archive-keyring.gpg
gpg --batch --yes --armor --export "$fpr" > orac-archive-keyring.asc

# Fail the publish rather than ship something apt would reject.
gpgv --keyring ./orac-archive-keyring.gpg "dists/$suite/InRelease"
echo "build-repo: signed with $fpr"
