#!/bin/sh
# Build orac-branding_<version>_all.deb into the repo's dist/ (gitignored).
# Needs only dpkg-deb; no debhelper, no root.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=${1:-"$here/../../dist"}
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

cp -a "$here/root/." "$stage/"
mkdir -p "$stage/DEBIAN"
cp "$here/DEBIAN/control" "$here/DEBIAN/postinst" "$here/DEBIAN/prerm" "$stage/DEBIAN/"
gzip -9n -c "$here/changelog" > "$stage/usr/share/doc/orac-branding/changelog.Debian.gz"

find "$stage" -type d -exec chmod 0755 {} +
find "$stage" -type f -exec chmod 0644 {} +
chmod 0755 "$stage/DEBIAN/postinst" "$stage/DEBIAN/prerm"
if [ -d "$stage/usr/bin" ]; then chmod 0755 "$stage"/usr/bin/*; fi

size=$(du -sk --exclude=DEBIAN "$stage" | cut -f1)
sed -i "/^Architecture:/a Installed-Size: $size" "$stage/DEBIAN/control"
(cd "$stage" && find . -type f ! -path './DEBIAN/*' -printf '%P\0' | sort -z | xargs -0 md5sum) > "$stage/DEBIAN/md5sums"
chmod 0644 "$stage/DEBIAN/md5sums"

version=$(sed -n 's/^Version: //p' "$stage/DEBIAN/control")
mkdir -p "$out"
dpkg-deb --root-owner-group -Zxz --build "$stage" "$out/orac-branding_${version}_all.deb"
