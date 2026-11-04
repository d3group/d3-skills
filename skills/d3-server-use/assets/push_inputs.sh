#!/usr/bin/env bash
# Send the server's inputs from the laptop, through the bucket when the project has one, else by rsync. Git carries
# code; small text files that belong in the repository may come with it, the inputs come by this script.
#
#   with a bucket (S3_URI_DEFAULT set): upload into the bucket; the server then takes the inputs with the command
#     printed at the end (`uv run tools/d3run.py pull <paths> --checksum`, which verifies every file)
#   without one yet (SERVER_DEFAULT set): rsync them straight into the checkout on the server
#   When the bucket arrives, set S3_URI_DEFAULT and the script switches to it.
#
# Copy into the project as jobs/push_inputs.sh and set the values below once (from the site file). List the inputs
# in jobs/server_inputs.txt, one path per line (a file or a folder, relative to the repository root, '#' for
# comments). Every path must lie in one of the ALLOWED folders: data that an agreement keeps on the laptop never
# matches, so the script refuses it before anything is sent. Symbolic links are refused or skipped.
#
#   bash jobs/push_inputs.sh --check     # validate the list, print it and the route
#   bash jobs/push_inputs.sh             # dry run: what would be sent
#   bash jobs/push_inputs.sh --go        # send
#
# S3_URI, AWS_PROFILE, SERVER and SERVER_INPUTS in the environment override the values below.
set -euo pipefail

S3_URI_DEFAULT="s3://<bucket>/<prefix>"   # with a bucket: the project's folder in it (s3_prefix in the site file)
AWS_PROFILE_DEFAULT="default"              # with a bucket: the laptop's profile in ~/.aws/config (aws_profile)
SERVER_DEFAULT="<alias>:<proj>"            # without one: ssh alias and checkout on the server (ssh_alias, server_dir)
ALLOWED='^(data/raw/<folder>|data/raw/<other folder>)(/|$)'   # the folders the server may receive

cd "$(dirname "$0")/.."
list_file="${SERVER_INPUTS:-jobs/server_inputs.txt}"
s3="${S3_URI:-$S3_URI_DEFAULT}"
s3="${s3%/}"
profile="${AWS_PROFILE:-$AWS_PROFILE_DEFAULT}"
server="${SERVER:-$SERVER_DEFAULT}"
server="${server%/}"
die() { printf '%s\n' "$*" >&2; exit 2; }

case "$ALLOWED" in *"<"*) die "set ALLOWED at the top of $0 first" ;; esac
case "$s3" in
  *"<"*) case "$server" in
           *"<"*) die "set S3_URI_DEFAULT (with a bucket) or SERVER_DEFAULT (without one) at the top of $0 first" ;;
           *) route=rsync ;;
         esac ;;
  *) route=bucket ;;
esac
[ -f "$list_file" ] || die "no input list: $list_file"
[ $# -eq 0 ] || [ "$1" = --check ] || [ "$1" = --go ] || die "usage: bash $0 [--check | --go]"

list="$(grep -v -e '^[[:space:]]*#' -e '^[[:space:]]*$' "$list_file" | sed -e 's:/*$::' || true)"
[ -n "$list" ] || die "$list_file lists no paths"
bad="$(printf '%s\n' "$list" | grep -E -v "$ALLOWED" || true)"
up="$(printf '%s\n' "$list" | grep -E -e '(^|/)\.\.(/|$)' -e '^/' || true)"
[ -z "$bad$up" ] || die "refused, not inside an allowed input folder (nothing was sent):
$bad$up"
while IFS= read -r p; do
  [ -e "$p" ] || die "missing on the laptop: $p"
  [ ! -L "$p" ] || die "refused, a symbolic link (list the real path): $p"
done <<< "$list"
if [ "${1:-}" = --check ]; then
  printf '%s\n' "$list"
  if [ "$route" = bucket ]; then echo "route: bucket $s3"; else echo "route: rsync to $server (no bucket set)"; fi
  exit 0
fi
go=no; [ "${1:-}" = --go ] && go=yes

if [ "$route" = rsync ]; then
  dry=(--dry-run --itemize-changes); [ $go = yes ] && dry=()
  printf '%s\n' "$list" | rsync -a -r --no-links --files-from=- ${dry[@]+"${dry[@]}"} ./ "$server/"
  if [ $go = yes ]; then echo "sent by rsync to $server"; else echo "dry run: nothing sent; run again with --go"; fi
  exit 0
fi

dry=(--dryrun); [ $go = yes ] && dry=()
while IFS= read -r p; do
  if [ -d "$p" ]; then
    aws s3 cp "$p" "$s3/$p/" --recursive --no-follow-symlinks --profile "$profile" --only-show-errors \
      ${dry[@]+"${dry[@]}"}
  else
    aws s3 cp "$p" "$s3/$p" --profile "$profile" --only-show-errors ${dry[@]+"${dry[@]}"}
  fi
  [ $go = no ] || echo "uploaded $p"
done <<< "$list"

pull="uv run tools/d3run.py pull"
while IFS= read -r p; do pull="$pull $(printf '%q' "$p")"; done <<< "$list"
if [ $go = yes ]; then
  echo "now on the login host, in the checkout (add --submit above 1 GB or 2,000 files):"
else
  echo "dry run: nothing uploaded; run again with --go. Then on the login host, in the checkout:"
fi
echo "  $pull --checksum"
