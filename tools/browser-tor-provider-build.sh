#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"
provider_root="$root/providers/arti"
log="$root/logs/arti-cargo-install.log"

mkdir -p "$root/logs"
mkdir -p "$root/providers"

cargo install arti --locked --root "$provider_root" >"$log" 2>&1

binary="$provider_root/bin/arti"
if [ ! -x "$binary" ]; then
  printf 'missing arti binary after install: %s\n' "$binary" >&2
  exit 1
fi

version="$("$binary" --version | head -n 1)"
printf 'AMPB_TOR_PROVIDER status=ok kind=arti binary=%s log=%s version="%s"\n' "$binary" "$log" "$version"
