#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"

mkdir -p "$root/src"
mkdir -p "$root/obj"
mkdir -p "$root/cache"
mkdir -p "$root/artifacts"
mkdir -p "$root/logs"

printf 'AMPB_BROWSER_BUILD_ROOT=%s\n' "$root"
printf 'AMPB_BROWSER_SRC=%s\n' "$root/src"
printf 'AMPB_BROWSER_OBJ=%s\n' "$root/obj"
printf 'AMPB_BROWSER_CACHE=%s\n' "$root/cache"
printf 'AMPB_BROWSER_ARTIFACTS=%s\n' "$root/artifacts"
printf 'AMPB_BROWSER_LOGS=%s\n' "$root/logs"
