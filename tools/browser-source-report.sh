#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"

report_repo() {
  label="$1"
  path="$2"
  if [ -d "$path/.git" ]; then
    printf '%s_DIR=%s\n' "$label" "$path"
    printf '%s_REMOTE=%s\n' "$label" "$(git -C "$path" remote get-url origin)"
    printf '%s_REV=%s\n' "$label" "$(git -C "$path" rev-parse --short HEAD)"
  else
    printf '%s_DIR=%s\n' "$label" "$path"
    printf '%s_STATUS=missing\n' "$label"
  fi
}

report_repo AMPB_GECKO "$root/src/gecko-dev"
report_repo AMPB_TOR_BROWSER_BUILD "$root/src/tor-browser-build"
report_repo AMPB_LEGACY_FIREFOX_ANDROID "$root/src/firefox-android"
