#!/bin/bash
set -euo pipefail
umask 027

# The forced SSH command accepts only the expected hash of the public main page.
IFS= read -r expected
[[ "$expected" =~ ^[0-9a-f]{64}$ ]] || exit 2
cd /clouddream/yingji-website
exec 9>/run/lock/yingji-website.lock
flock -w 30 9
page=$(mktemp .index-XXXXXX)
trap 'rm -f "$page"' EXIT
curl -q --fail --silent --show-error --location --retry 2 --max-time 45 \
  -H 'Accept: application/vnd.github.raw+json' \
  "https://api.github.com/repos/angrypandahu/yingji-releases/contents/website/index.html?ref=main&sha256=$expected" -o "$page"
echo "$expected  $page" | sha256sum --check --status
chmod --reference=index.html "$page"
backup=/var/backups/yingji-website/index.previous.html
install -d -m 0700 /var/backups/yingji-website
cp -p index.html "$backup.pending"
mv -f "$backup.pending" "$backup"
mv -f "$page" index.html
if ! actual=$(curl -qfsS --max-time 15 http://172.17.0.1:18090/ | sha256sum) || [[ "${actual%% *}" != "$expected" ]]; then
  cp -p "$backup" "$page"
  mv -f "$page" index.html
  echo 'Website health check failed; previous page restored' >&2
  exit 1
fi
echo "ECS website deployed and verified: $expected"
