#!/usr/bin/env bash
#
# tag_release.sh — Create a signed Git tag by default, or annotated tag if --no-sign is specified.
#
# Usage:
#   ./tag_release.sh [<tag-version>] [--no-sign] [--no-edit] [--date YYYY-MM-DD]
#
# Examples:
#   ./tag_release.sh               # Signed tag (default)
#   ./tag_release.sh v0.2.0        # Signed tag v0.2.0
#   ./tag_release.sh 0.3.0 --no-sign --no-edit  # Annotated tag (no-sign) without opening editor
#
set -euo pipefail

die() { echo "Error: $*" >&2; exit 1; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

read_version_from_pyproject() {
  if have_cmd python; then
    python - <<'PY'
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)
ver = data.get("project", {}).get("version")
if not ver:
    sys.exit("Missing [project].version in pyproject.toml")
print(ver)
PY
  else
    grep -E '^\s*version\s*=\s*".*"' pyproject.toml | head -n1 | sed -E 's/^.*"([^"]+)".*$/\1/'
  fi
}

normalize_tag() {
  local raw="$1"
  if [[ "$raw" =~ ^v[0-9] ]]; then
    echo "$raw"
  else
    echo "v${raw}"
  fi
}

today_iso() { date +%Y-%m-%d; }

ensure_clean_tree() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Warning: you have uncommitted changes."
    read -r -p "Continue anyway? [y/N] " ans
    [[ "${ans:-N}" =~ ^[Yy]$ ]] || exit 1
  fi
}

ensure_tag_absent() {
  local tag="$1"
  if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    die "Tag '$tag' already exists."
  fi
}

# ---- Parse args ----
TAG_INPUT="${1-}"
shift || true

SIGN_MODE="signed"   # default is signed
NO_EDIT=false
DATE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-sign)  SIGN_MODE="annotated" ;;
    --no-edit)  NO_EDIT=true ;;
    --date)     DATE_OVERRIDE="${2-}"; shift ;;
    *)          die "Unknown option: $1" ;;
  esac
  shift
done

# ---- Determine version/tag/date ----
if [[ -z "$TAG_INPUT" ]]; then
  VERSION="$(read_version_from_pyproject)"
else
  VERSION="${TAG_INPUT#v}"
fi

[[ -n "${DATE_OVERRIDE}" ]] && REL_DATE="${DATE_OVERRIDE}" || REL_DATE="$(today_iso)"
TAG="$(normalize_tag "$VERSION")"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not a git repository."
ensure_clean_tree
ensure_tag_absent "$TAG"

# ---- Default message template ----
read -r -d '' MSG_DEFAULT <<EOF || true
Static-Fire Toolkit ${TAG} (${REL_DATE})

Summary
- Short summary of this release. (e.g., First public release; MVP pipeline)

Highlights
- Key features or improvements

Breaking Changes
- List any API breaks

Fixes
- Notable bug fixes

Docs
- Documentation updates

Thanks
- SNU Rocket Team Hanaro contributors

Artifacts
- PyPI: static-fire-toolkit==${VERSION}
- Tag: ${TAG}
EOF

TMPMSG="$(mktemp -t tagmsg.XXXXXX)"
printf "%s\n" "$MSG_DEFAULT" > "$TMPMSG"

if [[ "$NO_EDIT" == false ]]; then
  : "${EDITOR:=vi}"
  "$EDITOR" "$TMPMSG"
fi

# ---- Create tag ----
if [[ "$SIGN_MODE" == "signed" ]]; then
  echo "Creating SIGNED tag ${TAG} ..."
  git tag -s "$TAG" -F "$TMPMSG"
else
  echo "Creating ANNOTATED (no-sign) tag ${TAG} ..."
  git tag -a "$TAG" -F "$TMPMSG"
fi

rm -f "$TMPMSG"
