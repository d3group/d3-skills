# Data and storage

The server home is small (warning above 100 GB, hard limit 200 GB), on NFS, and has no backups. The S3 bucket on the
KiRegio storage (MinIO) is the store; the server keeps only what running jobs need.

## Contents
1. What lives where
2. Setting up the AWS CLI
3. Layout in the bucket
4. Moving data with d3run
5. A round's data cycle
6. Cleaning up
7. Without a bucket: rsync, git, other storage
8. Speed and small files
9. Sensitive data

## 1. What lives where

| Kind | Server | S3 |
|---|---|---|
| Code | git checkout `<proj>` | no (GitHub) |
| Environment | `<proj>/.venv`, uv cache (prune it) | no |
| Raw, pre- and postprocessed data | only the datasets of the current round, pulled once per round | all of it |
| Checkpoints | the newest one per active run | the newest two per run |
| Logs, results | until `archive --clean` | all of it |
| Registry `runs/registry.db` | the working copy | a daily snapshot (`registry/`) |

## 2. Setting up the AWS CLI

Look first, set up only what is missing (SKILL.md, step 0.3): `aws --version`, `aws configure list` and the
sections and `endpoint_url` lines of `~/.aws/config`, on the laptop and on the server. `~/.aws/credentials` is the
user's file: never open, print or copy it. The answers (bucket, endpoint, profile, project prefixes, the date of a
working `aws s3 ls`) go into `<site>`.

The group uses the AWS CLI (no `mc`; it is archived upstream). On the laptop and on the server:

```bash
uv tool install awscli            # on the server it lands in ~/.local/bin/aws; call it by full path in scripts
```

`~/.aws/config` (endpoint from the admin, stored in `<site>` as `endpoint_url`):

```ini
[default]
region = us-east-1
endpoint_url = <S3 API endpoint from the admin, not the web console>
s3 =
    addressing_style = path
    max_concurrent_requests = 32
```

`~/.aws/credentials` with `chmod 600`, **written by the user**, never by Claude, never in a repo or note:

```ini
[default]
aws_access_key_id = …
aws_secret_access_key = …
```

- Test: `aws s3 ls s3://<bucket>/` (laptop and login host).
- With a named profile instead of `[default]`, keys given as environment variables are ignored; `[default]` keeps
  both ways open. Tell `d3run.py init` about a profile with `--aws-profile`.
- Never create buckets: one bucket per user, one folder per project inside it.
- "Access Denied" right after the admin created the key: the key's policy may be wrong (a stray space in the bucket
  ARN happened once); only the admin can fix access keys.

## 3. Layout in the bucket

```
s3://<bucket>/<project>/            # mirrors the repository
    data/raw/ …                     # d3run.py push data/raw
    data/processed/ …
    runs/<run_id>/                  # one folder per run, same as on the server
        run.json  status.json  archive.json  config.yaml
        logs/attempt-01-<jobid>.out|err  gpu-<jobid>.csv
        checkpoints/step-…/  LATEST.json
        results/ …
    registry/registry-YYYYMMDD.db   # daily snapshot of runs/registry.db
```

## 4. Moving data with d3run

| Command | Does |
|---|---|
| `push data/raw [--clean]` | upload a project path, compare every file's size (and with `--clean` its MD5), optionally delete the local copy |
| `pull data/raw [--checksum]` | download it again (same layout), compare sizes (and MD5) |
| `archive <ids…> \| --tag T \| --finished [--clean]` | upload run folders; `--clean` keeps only the three JSON files |
| `--submit` (any of the three) | run the transfer as a 2-CPU Slurm job; required above 1 GB or 2,000 files |
| `usage` | size of each run folder and of `data/`, `results/`, `logs/` |

Safety rules built in: nothing is deleted before every file is verified in S3, by size and, with `--clean`, by
MD5 against the object's ETag (for files from 8 MB on the multipart ETag, computed the way the AWS CLI uploads:
8 MB parts). `--size-only` skips the checksum and is for when the user asks for it. If `~/.aws/config` sets another
`multipart_chunksize`, export `D3RUN_S3_CHUNK_MB` with the same value, otherwise the check fails and nothing is
deleted. Runs that are queued or running are uploaded but never cleaned; paths tracked by git and the registry are
never cleaned.

Inside jobs, `d3job` uploads each checkpoint and, at `finish()`, the results. Logs are uploaded by `archive` after
the attempt, because a log is still open while its job runs.

## 5. A round's data cycle

1. `pull` the datasets the round needs into `data/` once (as a `--submit` job if large). All jobs read that one copy;
   never let a hundred jobs download the same file.
2. Preprocessing jobs write to `data/processed/`; `push` it when done.
3. Run the round; jobs upload checkpoints and results themselves.
4. After the round: `archive --finished --clean --submit`, then `push data/… --clean` for what the next round does
   not need, then `usage`.

## 6. Cleaning up

- After every round, and whenever `usage` passes about 50 GB.
- `uv cache prune` after environment changes; old `.venv`s of deleted projects go too.
- Never scan the whole home, not even in a job: `du` or `find` over `~` asks the shared NFS server about every file.
  The total is in Grafana, run folders in `d3run.py usage`, one folder at a time with `du -sh <folder>`.
- **Before the store is the only copy:** check once that the bucket keeps objects
  (`aws s3api get-bucket-lifecycle-configuration --bucket <bucket>`; an expiry rule means ask the admin), and run a
  restore drill: `d3run.py pull runs/<id> --checksum` for one cleaned run, open its results, clean it again.
- Cleaning is deleting: before the first `--clean` of a session, show the user what will go (`archive … ` without
  `--clean` prints what is verified) and get a yes.

## 7. Without a bucket: rsync, git, other storage

Until the admin has set up a bucket, the user's own computer is the store. The server still deletes nothing that
is not verified in a copy: `d3run.py manifest` lists files and sizes, `d3run.py clean --manifest` compares the
server's files with the copy's list and deletes only when every file is there with the same size.

**rsync to the user's computer (default).** Everything goes there: runs (logs, checkpoints, results), and the
data folders the next round does not need. Run on the laptop, in a folder of the user's choice (e.g.
`~/d3-archive/<project>`):

```bash
ssh <alias> 'cd <proj> && uv run tools/d3run.py manifest --finished --list' > list.txt   # finished runs (paths only)
echo data/processed >> list.txt                                                          # plus data paths
rsync -a -r --files-from=list.txt <alias>:<proj>/ ~/d3-archive/<project>/                # copy (macOS rsync works)
uv run <skill-dir>/scripts/d3run.py manifest --root ~/d3-archive/<project> $(cat list.txt) > copy.json
ssh <alias> 'cd <proj> && uv run tools/d3run.py clean --manifest - --copied-to "laptop:~/d3-archive/<project>"' < copy.json
```

- The manifest of the copy holds size and SHA-256 per file; `clean` hashes the server's files (above 1 GB as a
  Slurm job, `--submit`) and deletes only on a match. A manifest made with `--size-only` is refused unless `clean`
  also gets `--size-only`.
- `clean` keeps `run.json`, `status.json` and `archive.json` of each run on the server (the registry and
  `list` show where the copy lives), never touches queued or running runs, and refuses paths tracked by git.
  Above 2,000 files add `--submit`: the deletion runs as a Slurm job.
- A run whose copy differs in one file stays on the server; rerun rsync and the manifest, then `clean` again.
- To resume or post-process a run later, rsync it back (`rsync -a ~/d3-archive/<project>/runs/<id>/
  <alias>:<proj>/runs/<id>/`).
- Without a bucket, `d3job` keeps two checkpoints per active run on the server; they reach the laptop with the
  run folder.

**git for small results.** Text results that belong in the repository anyway (summary tables, reports, small
figures) can be committed on the server, pushed, and pulled on the laptop. Only small files without personal
data, and never as a way to move checkpoints, logs or data (no large files in git, no git-lfs). Tracked files stay
in the checkout, so git moves results to the laptop but does not free space on the server.

**Other storage as a fallback.** A university share, a NAS, or the user's own cloud storage work the same way:
copy the paths there, run `d3run.py manifest --root <that copy>` where the copy is mounted, and pass the result
to `clean --manifest` with `--copied-to <where>`. Own cloud storage only for data without restrictions
(section 9).

Ask again for the bucket now and then; once it exists, set it with `d3run.py init --s3-uri …`, record
`has_bucket = "yes"` in `<site>`, and push the laptop archive to S3 if the user wants one store.

## 8. Speed and small files

Measured on this storage: 10 GB of large files took about 7 minutes; 0.7 GB in 50,000 small log files took about
65 minutes; listing 370,000 keys took about 14 minutes. File count dominates. Pack many small files (one SQLite or
Parquet per job, `tar` for log folders that are only archived) before they reach NFS or S3.

## 9. Sensitive data

Personal data, partner data and anything under a data agreement go only to storage on university infrastructure
(the server, the bucket, the work laptop) and wherever the agreement allows. Never to GitHub, never to personal cloud storage, never into
an issue or a chat. Own cloud storage (section 7) is a fallback for everything else. Large files never go into
git at all (no git-lfs either): they go to S3, and the repository lists them in `.gitignore`.
