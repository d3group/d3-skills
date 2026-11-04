#!/usr/bin/env bash
# Upload the server's inputs from the laptop into the bucket. The bucket is the only way data reaches the server: git
# carries code, never data. The server then takes the inputs with the command this script prints at the end
# (`uv run tools/d3run.py pull <paths> --checksum`, which verifies every file against the bucket).
#
# Copy into the project as jobs/push_inputs.sh and set the three values below once (from the site file). List the
# inputs in jobs/server_inputs.txt, one path per line (a file or a folder, relative to the repository root, '#' for
# comments). Every path must lie in one of the ALLOWED folders: data that an agreement keeps on the laptop never
# matches, so the script refuses it before anything is uploaded. Symbolic links are refused or skipped.
#
#   bash jobs/push_inputs.sh --check     # validate the list, print it
#   bash jobs/push_inputs.sh             # dry run: what would be uploaded
#   bash jobs/push_inputs.sh --go        # upload
#
# S3_URI, AWS_PROFILE and SERVER_INPUTS in the environment override the values below.
set -euo pipefail

S3_URI_DEFAULT="s3://<bucket>/<prefix>"   # the project's folder in the bucket (s3_prefix in the site file)
AWS_PROFILE_DEFAULT="default"              # the laptop's profile in ~/.aws/config (aws_profile in the site file)
ALLOWED='^(data/raw/<folder>|data/raw/<other folder>)(/|$)'   # the folders the server may receive

cd "$(dirname "$0")/.."
list_file="${SERVER_INPUTS:-jobs/server_inputs.txt}"
s3="${S3_URI:-$S3_URI_DEFAULT}"
s3="${s3%/}"
profile="${AWS_PROFILE:-$AWS_PROFILE_DEFAULT}"
die() { printf '%s\n' "$*" >&2; exit 2; }

case "$s3$ALLOWED" in *"<"*) die "set S3_URI_DEFAULT and ALLOWED at the top of $0 first" ;; esac
[ -f "$list_file" ] || die "no input list: $list_file"
[ $# -eq 0 ] || [ "$1" = --check ] || [ "$1" = --go ] || die "usage: bash $0 [--check | --go]"

list="$(grep -v -e '^[[:space:]]*#' -e '^[[:space:]]*$' "$list_file" | sed -e 's:/*$::' || true)"
[ -n "$list" ] || die "$list_file lists no paths"
bad="$(printf '%s\n' "$list" | grep -E -v "$ALLOWED" || true)"
up="$(printf '%s\n' "$list" | grep -E -e '(^|/)\.\.(/|$)' -e '^/' || true)"
[ -z "$bad$up" ] || die "refused, not inside an allowed input folder (nothing was uploaded):
$bad$up"
while IFS= read -r p; do
  [ -e "$p" ] || die "missing on the laptop: $p"
  [ ! -L "$p" ] || die "refused, a symbolic link (list the real path): $p"
done <<< "$list"
if [ "${1:-}" = --check ]; then printf '%s\n' "$list"; exit 0; fi

dry=(--dryrun); [ "${1:-}" = --go ] && dry=()
while IFS= read -r p; do
  if [ -d "$p" ]; then
    aws s3 cp "$p" "$s3/$p/" --recursive --no-follow-symlinks --profile "$profile" --only-show-errors \
      ${dry[@]+"${dry[@]}"}
  else
    aws s3 cp "$p" "$s3/$p" --profile "$profile" --only-show-errors ${dry[@]+"${dry[@]}"}
  fi
  [ ${#dry[@]} -gt 0 ] || echo "uploaded $p"
done <<< "$list"

pull="uv run tools/d3run.py pull"
while IFS= read -r p; do pull="$pull $(printf '%q' "$p")"; done <<< "$list"
if [ ${#dry[@]} -eq 0 ]; then
  echo "now on the login host, in the checkout (add --submit above 1 GB or 2,000 files):"
else
  echo "dry run: nothing uploaded; run again with --go. Then on the login host, in the checkout:"
fi
echo "  $pull --checksum"
