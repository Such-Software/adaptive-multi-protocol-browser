#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"
gecko_dir="$root/src/gecko-dev"
log="$root/logs/gecko-android-mach-probe.log"

if [ ! -d "$gecko_dir" ]; then
  printf 'missing gecko checkout: %s\n' "$gecko_dir" >&2
  exit 1
fi

mkdir -p "$root/cache/gradle"
mkdir -p "$root/cache/mozbuild"
mkdir -p "$root/cache/pip"
mkdir -p "$root/cache/pycache"
mkdir -p "$root/logs"

cd "$gecko_dir"

MOZBUILD_STATE_PATH="$root/cache/mozbuild" \
GRADLE_USER_HOME="$root/cache/gradle" \
PIP_CACHE_DIR="$root/cache/pip" \
PYTHONPYCACHEPREFIX="$root/cache/pycache" \
  ./mach build mobile/android --help >"$log" 2>&1

printf 'AMPB_ANDROID_BUILD_PROBE status=ok log=%s\n' "$log"
