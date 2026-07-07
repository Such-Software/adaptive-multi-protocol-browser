#!/bin/sh
set -eu

root="${AMPB_BROWSER_BUILD_ROOT:-/tmp/ampb-browser-build}"
gecko_dir="$root/src/gecko-dev"
mode="${AMPB_DESKTOP_BUILD_PROBE_MODE:-help}"
flavor="${AMPB_DESKTOP_BUILD_FLAVOR:-source}"
log="$root/logs/gecko-desktop-${flavor}-mach-${mode}.log"
mozconfig="$root/mozconfigs/desktop-${flavor}.mozconfig"
objdir="$root/obj/gecko-desktop-${flavor}"

if [ ! -d "$gecko_dir" ]; then
  printf 'missing gecko checkout: %s\n' "$gecko_dir" >&2
  exit 1
fi

mkdir -p "$root/cache/gradle"
mkdir -p "$root/cache/mozbuild"
mkdir -p "$root/cache/pip"
mkdir -p "$root/cache/pycache"
mkdir -p "$root/logs"
mkdir -p "$root/mozconfigs"
mkdir -p "$objdir"

cat >"$mozconfig" <<EOF
mk_add_options MOZ_OBJDIR=$objdir
ac_add_options --enable-application=browser
ac_add_options --disable-crashreporter
ac_add_options --disable-debug
EOF

if [ "$flavor" = "artifact" ]; then
  printf '%s\n' 'ac_add_options --enable-artifact-builds' >>"$mozconfig"
elif [ "$flavor" != "source" ]; then
  printf 'unsupported AMPB_DESKTOP_BUILD_FLAVOR: %s\n' "$flavor" >&2
  exit 2
else
  printf '%s\n' 'ac_add_options --enable-optimize' >>"$mozconfig"
fi

cd "$gecko_dir"

mach_env() {
  MOZCONFIG="$mozconfig" \
  MOZBUILD_STATE_PATH="$root/cache/mozbuild" \
  GRADLE_USER_HOME="$root/cache/gradle" \
  PIP_CACHE_DIR="$root/cache/pip" \
  PYTHONPYCACHEPREFIX="$root/cache/pycache" \
    "$@"
}

ensure_zstandard() {
  for python_bin in "$root"/cache/mozbuild/srcdirs/*/_virtualenvs/build/bin/python "$root"/cache/mozbuild/srcdirs/*/_virtualenvs/common/bin/python; do
    [ -x "$python_bin" ] || continue
    if "$python_bin" -c 'import zstandard' >/dev/null 2>&1; then
      continue
    fi
    PIP_CACHE_DIR="$root/cache/pip" "$python_bin" -m pip install 'zstandard<=0.23.0,>=0.11.1'
  done
}

case "$mode" in
  help)
    mach_env ./mach build --help >"$log" 2>&1
    ;;
  configure)
    mach_env ./mach build --help >/dev/null 2>&1
    ensure_zstandard
    mach_env ./mach configure >"$log" 2>&1
    ;;
  build)
    mach_env ./mach build --help >/dev/null 2>&1
    ensure_zstandard
    mach_env ./mach build >"$log" 2>&1
    ;;
  *)
    printf 'unsupported AMPB_DESKTOP_BUILD_PROBE_MODE: %s\n' "$mode" >&2
    exit 2
    ;;
esac

printf 'AMPB_DESKTOP_BUILD_PROBE status=ok mode=%s flavor=%s mozconfig=%s objdir=%s log=%s\n' "$mode" "$flavor" "$mozconfig" "$objdir" "$log"
