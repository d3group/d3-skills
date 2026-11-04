#!/bin/bash
# Job template for the KiRegio server (d3-server-use skill). Copy it into the project, e.g. jobs/train.sbatch.
#
# Submit through d3run.py, which sets --job-name, --time, --cpus-per-task, --mem, --gres, --output, --error,
# --signal and the D3RUN_* variables on the command line (they override the #SBATCH defaults below):
#   uv run tools/d3run.py submit <run_id> --script jobs/train.sbatch --time 06:00:00 --cpus 1 --mem 8G --gpus 1 \
#       -- --config configs/x.yaml
# A plain `sbatch jobs/train.sbatch` also works with the defaults below (smoke tests, one-off jobs) once
# `mkdir -p logs/slurm` has run: Slurm does not create the --output folder, and the job fails without a log.
#
# No --partition: GPU jobs go to main and CPU-only jobs to cpu by themselves. For a GPU job add
# `--gpus 1` to the submit call (or a `#SBATCH --gres=gpu:1` line below).
# Slurm reads #SBATCH lines only up to the first command, so all of them stay in this block.
#SBATCH --job-name=train
#SBATCH --time=00:15:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --signal=B:USR1@600
#SBATCH --output=logs/slurm/%x-%j.out
#SBATCH --error=logs/slurm/%x-%j.err

set -uo pipefail
export D3RUN_JOB_START=$(date +%s)              # the job's clock starts here, before uv and imports
cd "${SLURM_SUBMIT_DIR:-$PWD}"

export PYTHONUNBUFFERED=1
# export JAX_PLATFORMS=cpu                      # CPU-only job with JAX: skip the CUDA plugin
# export XLA_PYTHON_CLIENT_MEM_FRACTION=0.95    # one large JAX model per GPU

RUN_DIR="${D3RUN_DIR:-runs/local}"
mkdir -p "$RUN_DIR/logs"
rm -f "$RUN_DIR/STOP"
echo "[d3] run=${D3RUN_ID:-none} attempt=${D3RUN_ATTEMPT:-0} job=${SLURM_JOB_ID:-none} host=$(hostname) start=$(date -Iseconds)"

# Slurm sends USR1 to this shell LEAD seconds before the limit (--signal=B:USR1@600; d3run passes its
# lead as D3RUN_SIGNAL_LEAD_S). The trap writes the confirmed end time into STOP. RunContext reads it and
# still uses the time up to its measured margin (step + checkpoint), so the job does not stop early, and
# no signal has to pass through `uv run` to Python.
LEAD="${D3RUN_SIGNAL_LEAD_S:-600}"
trap 'echo "[d3] USR1: the limit is about ${LEAD} s away"; echo $(( $(date +%s) + LEAD )) > "$RUN_DIR/STOP"' USR1

# GPU memory, one line per minute, read by `d3run.py reconcile` and `size` (GPU jobs only)
GPU_LOG_PID=""
if [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]] && command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu --format=csv,noheader,nounits -l 60 \
    > "$RUN_DIR/logs/gpu-${SLURM_JOB_ID:-local}.csv" 2>/dev/null &
  GPU_LOG_PID=$!
fi

# The environment was synced once on the login host (`uv sync`), so the jobs do not all sync it at once.
# The program runs in the background so that the trap above can run while it works.
uv run --no-sync python -u src/train.py "$@" &
CHILD=$!
while :; do
  wait "$CHILD"; RC=$?
  # `wait` returns early (status > 128) when the trap ran; keep waiting while the program lives.
  if (( RC > 128 )) && kill -0 "$CHILD" 2>/dev/null; then continue; fi
  break
done

[[ -n "$GPU_LOG_PID" ]] && kill "$GPU_LOG_PID" 2>/dev/null
echo "[d3] exit=$RC end=$(date -Iseconds)"
exit "$RC"
