#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"
src="$root/src"

gecko_repo="${AMPB_GECKO_REPO:-https://github.com/mozilla/gecko-dev.git}"
legacy_android_repo="${AMPB_LEGACY_FIREFOX_ANDROID_REPO:-https://github.com/mozilla-mobile/firefox-android.git}"
tor_build_repo="${AMPB_TOR_BROWSER_BUILD_REPO:-https://gitlab.torproject.org/tpo/applications/tor-browser-build.git}"

mkdir -p "$src"

sync_repo() {
  repo_url="$1"
  dest="$2"
  mode="$3"
  if [ -d "$dest/.git" ]; then
    if [ "$mode" = "blobless" ]; then
      git -C "$dest" fetch --depth 1 --filter=blob:none origin
    else
      git -C "$dest" fetch --depth 1 origin
    fi
    git -C "$dest" reset --hard FETCH_HEAD
  else
    if [ "$mode" = "blobless" ]; then
      git clone --depth 1 --filter=blob:none "$repo_url" "$dest"
    else
      git clone --depth 1 "$repo_url" "$dest"
    fi
  fi
}

sync_repo "$gecko_repo" "$src/gecko-dev" "blobless"
sync_repo "$tor_build_repo" "$src/tor-browser-build" "normal"

if [ "${AMPB_INCLUDE_LEGACY_FIREFOX_ANDROID:-0}" = "1" ]; then
  sync_repo "$legacy_android_repo" "$src/firefox-android" "normal"
fi

printf 'AMPB_SOURCE_SYNC status=ok root=%s\n' "$root"
