# Pitfalls on this server

Symptom, cause, fix. Most were met in practice.

| Symptom | Cause | Fix |
|---|---|---|
| The server stops answering; new ssh sessions hang after login | heavy work on the login host (a polars scan used every core and saturated memory and disk) | everything that reads data or trains goes into a Slurm job; on the login host only light commands. If a remote command hangs, assume your own process first and kill it |
| Job pending forever, reason `PartitionTimeLimit` | `--time` above 24 h (e.g. old scripts with 48 h) | at most 24 h; checkpoints and segments |
| `sbatch` rejected right away | `--partition=main` without a GPU, or `--partition=cpu` with one | leave `--partition` out |
| Your jobs hold all GPUs while a colleague waits hours | no preemption: running jobs keep their GPUs until they end | `d3run.py submit` keeps a share free while others wait, `feed` releases the rest later; shorter GPU segments when the group is busy (cluster.md, section 4) |
| CPU jobs pending although CPUs are free | your own pending GPU jobs rank higher and hold the node; backfill tests only 100 of your jobs | submit CPU jobs first; `nice` on the GPU jobs (cluster.md, section 3) |
| Job runs older code than expected | the code changed on the server between submission and start | never pull while a round is queued; `d3run.py show` lists the commit |
| Job fails at once without any log | the `--output` folder does not exist (Slurm does not create it) | create it, or submit with `d3run.py`, which writes into the run folder |
| Many jobs fail at start with uv lock or resolution errors | each job's `uv run` syncs the shared `.venv` at the same time | `uv sync` once on the login host, `uv run --no-sync` in jobs |
| "No GPU" in a check on the login host | the login host has no GPU; GPUs are visible only inside jobs | check `jax.devices()` / `torch.cuda.is_available()` inside a job; GPU load via `/home/.cluster-status/nvidia-smi.txt` |
| A JAX job seems to use 75 % of a GPU | JAX preallocates GPU memory | measure with `XLA_PYTHON_CLIENT_PREALLOCATE=false` in the pilot |
| CUDA plugin traceback in a CPU job's log | JAX looks for CUDA before falling back | harmless; `JAX_PLATFORMS=cpu` silences it |
| A Slurm job ID points to the wrong experiment | job IDs restarted with the rebuild (about 3,000 again) | key everything by run ID; `find-job` lists every match with its submit time |
| Registry corrupt or "database is locked" | SQLite written from login host and compute node at once (WAL over NFS) | one writer: only `d3run.py` on the login host writes |
| Unpacking or copying a folder takes hours | NFS creates about 30 small files per second from a job | pack small files (SQLite, Parquet, tar) |
| Home above the quota warning | runs, checkpoints, data and old `.venv`s pile up; no automatic cleanup | `d3run.py usage`, `archive --finished --clean --submit`, `uv cache prune` |
| `sqlite3: command not found` on the server | no sqlite3 CLI | read databases with Python (`uv run python -c …`) or `d3run.py show/list` |
| `gpu-status` prints nothing or garbles | it runs `watch` and needs a terminal | `ssh -t <alias> gpu-status`, or read the file directly |
| Background watcher on the laptop never fires | zsh does not split `ssh $OPTS host`; macOS has no `timeout`; errors hidden by `2>/dev/null` | ssh options as an array (`O=(-o BatchMode=yes); ssh "${O[@]}" …`) or inline; bound ssh with `ConnectTimeout`/`ServerAliveInterval`; run loops with `bash`; print failed checks; test the empty-queue path once in the foreground |
| Old `sq` alias behaves differently | an alias from an old `.bashrc` shadows the system `sq` | remove the alias |
| `git` commands fail with an LFS filter error | an old `~/.gitconfig` still requires git-lfs, which the server does not have | remove the `[filter "lfs"]` block, or use a repository without LFS |
| JupyterHub link does not open | http no longer works | https on port 8000, and import the CA certificate |
