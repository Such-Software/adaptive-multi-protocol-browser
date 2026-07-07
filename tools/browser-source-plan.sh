#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"

gecko_repo="${AMPB_GECKO_REPO:-https://github.com/mozilla/gecko-dev.git}"
legacy_android_repo="${AMPB_LEGACY_FIREFOX_ANDROID_REPO:-https://github.com/mozilla-mobile/firefox-android.git}"
tor_build_repo="${AMPB_TOR_BROWSER_BUILD_REPO:-https://gitlab.torproject.org/tpo/applications/tor-browser-build.git}"

printf 'AMPB_BROWSER_BUILD_ROOT=%s\n' "$root"
printf 'AMPB_GECKO_REPO=%s\n' "$gecko_repo"
printf 'AMPB_GECKO_DIR=%s\n' "$root/src/gecko-dev"
printf 'AMPB_LEGACY_FIREFOX_ANDROID_REPO=%s\n' "$legacy_android_repo"
printf 'AMPB_LEGACY_FIREFOX_ANDROID_DIR=%s\n' "$root/src/firefox-android"
printf 'AMPB_TOR_BROWSER_BUILD_REPO=%s\n' "$tor_build_repo"
printf 'AMPB_TOR_BROWSER_BUILD_DIR=%s\n' "$root/src/tor-browser-build"
printf 'AMPB_GRADLE_USER_HOME=%s\n' "$root/cache/gradle"
printf 'AMPB_MOZBUILD_STATE_PATH=%s\n' "$root/cache/mozbuild"
printf 'AMPB_BUILD_LOG=%s\n' "$root/logs/gecko-android-mach-probe.log"
