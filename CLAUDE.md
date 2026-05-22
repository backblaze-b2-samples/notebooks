# Backblaze B2 sample notebooks: conventions

This file documents repo-wide conventions for contributors (human or AI). New
example notebooks and CI workflows should follow these patterns.

## Writing style

* **No em dashes (U+2014) or en dashes (U+2013).** Use periods, commas,
  parentheses, or colons instead. Enforced mechanically by the
  `no-em-or-en-dash` pre-commit hook (see `scripts/forbid_em_dash.py`). The
  hook runs on every file type so READMEs, notebook markdown, Python
  comments, and YAML are all gated.

## Repository layout

Every example lives in its own top-level directory containing:

| File | Required | Purpose |
|---|---|---|
| `<name>.ipynb` | yes | The notebook itself. Title row carries Colab + Binder + Codespaces badges. |
| `README.md` | yes | Mirrors the structure of `ray-train-tune-checkpoints/README.md`: title + 3 badges, "What's in this directory", "Why this works", "Two distinct buckets", "Running the notebook (and where to put credentials)", "Related". |
| `requirements.txt` | yes | Alphabetical pip dependencies, one per line. The notebook's first `%pip install` cell must match this list exactly. |
| `prepare_dataset.py` | optional | Idempotent script to generate / upload the sample's seed data to B2. Used at repo-setup time and (optionally) at the top of CI. |

The repo root also has:

* `README.md`: index of all examples, with the same launch badges per entry.
* `.pre-commit-config.yaml`: lint + format hooks (see below).
* `.github/workflows/`: CI workflows (see below).
* `scripts/`: tiny helpers used by pre-commit or CI.

## Backblaze B2 patterns

### Two-bucket pattern

Every notebook uses two buckets:

* **Public read** for the seed dataset. Lives in a long-lived public bucket
  like `b2datasets` (for Ray Train) or `odh-datasets` (for cifar). Either
  anonymous or shipped with a pre-shared read-only application key.
* **Private write** for the user's outputs (checkpoints, transcripts,
  inference results). The user supplies their own bucket name + application
  key. Notebook prompts interactively for these unless env vars are set
  (see "Headless execution" below).

### Custom User-Agent on every B2 boto3 client

When constructing a `boto3.client("s3", ...)` against B2, always include a
custom `user_agent_extra` so server-side logs can attribute the traffic.

```python
boto3.client(
    "s3",
    endpoint_url=...,
    config=Config(
        signature_version="s3v4",
        user_agent_extra="b2-notebook-<notebook-slug>",
    ),
)
```

Recommended slug pattern: `b2-notebook-<short-name>` (e.g.
`b2-notebook-pytorch`, `b2-notebook-whisper`). When the same boto3 call
must accept a downstream user-agent override, append the user value rather
than replace ours (same shape as the dvc-s3 / clearml upstream patches we
landed elsewhere).

### Notebooks using pyarrow instead of boto3

For notebooks that go through `pyarrow.fs.S3FileSystem` (e.g.
`ray-train-tune-checkpoints/`), the Python binding does not currently expose
`user_agent_extra`. There is an upstream apache/arrow PR opportunity to fix
this; until it lands, accept the gap and don't try to work around it in the
notebook.

## Headless execution (CI compatibility)

Every interactive `input()` / `getpass()` call must support an env-var-first
fallback so CI (and Codespaces secret injection) can drive the notebook
without human intervention.

Idiom:

```python
YOUR_BUCKET = os.environ.get("PRIVATE_B2_BUCKET", "").strip()
if not YOUR_BUCKET:
    YOUR_BUCKET = input("Bucket name: ").strip()
```

Standard env vars across all example notebooks:

| Env var | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | B2 application key id / secret (standard AWS SDK names) |
| `B2_APPLICATION_KEY_ID` / `B2_APPLICATION_KEY` | Native Backblaze names; notebooks alias these onto the AWS-named pair |
| `AWS_ENDPOINT_URL_S3` | Full endpoint URL (used by Ray / pyarrow path) |
| `PRIVATE_B2_BUCKET` | Notebook output bucket (CI: `backblaze-samples-ci`) |
| `PRIVATE_B2_REGION` | B2 region for output bucket (CI: `us-west-001`) |
| `PRIVATE_B2_PREFIX` | Key prefix under the output bucket (CI: `ci/<notebook>/run-<gh_run_id>`) |

The interactive prompts remain for human use; the env vars take precedence
when set.

## Pre-commit hooks

Run locally with `pre-commit install` (once) + `pre-commit run --all-files`.
The same config runs in `.github/workflows/lint.yml` on every push.

| Hook | What it does |
|---|---|
| `trailing-whitespace`, `end-of-file-fixer`, `check-merge-conflict`, `check-yaml`, `check-json`, `mixed-line-ending` | Standard pre-commit-hooks hygiene |
| `nbstripout` | Strips notebook output cells before commit. Keeps diffs readable and prevents credential / bucket-name leakage from interactive runs. |
| `nbqa-ruff` | Lints Python code inside notebook cells. `E402` (top-level imports) and `E501` (line length) are ignored for tutorial-style code. |
| `codespell` | Typo catcher (notebooks are excluded; nbqa covers their code). |
| `no-em-or-en-dash` (local) | Forbids `U+2014` (em dash) and `U+2013` (en dash) repo-wide. |

If a hook modifies a file (e.g. nbstripout, end-of-file-fixer), pre-commit
exits non-zero. `git add` the changes and re-commit.

## CI workflows

### Per-notebook `test-<notebook>.yml`

Each notebook has its own workflow that:

1. Triggers on push / PR touching that notebook's directory (path filter).
2. Sets `PRIVATE_B2_BUCKET=backblaze-samples-ci`, `PRIVATE_B2_PREFIX=ci/<notebook>/run-<run_id>-<attempt>`, and the AWS-named credentials from repo secrets.
3. Installs the notebook's `requirements.txt` + `nbmake pytest awscli`.
4. Pre-seed-check (or fail-fast) for the public dataset.
5. Runs `pytest --nbmake --nbmake-timeout=<seconds> -v <notebook>.ipynb`.
6. Cleans up the per-run prefix with `aws s3 rm --recursive` (always, even on failure).

The single shared bucket `backblaze-samples-ci` is configured with a
lifecycle rule that auto-deletes anything under `ci/` after 2 days, so
even if cleanup fails the artifacts don't accumulate.

### `lint.yml`

Single workflow that:
1. Runs `pre-commit run --all-files` via `pre-commit/action@v3.0.1`.
2. Walks every `*.ipynb` and validates JSON + per-cell `ast.parse`.

Runs on every push to any branch.

## Secrets

Repository secrets used by CI workflows (`Settings` &rarr; `Secrets and variables` &rarr; `Actions`):

| Secret | Value |
|---|---|
| `CI_KEY_ID` | keyID of the `ci-notebooks-key` B2 application key, scoped to the `backblaze-samples-ci` bucket only. |
| `CI_APP_KEY` | applicationKey of the same. |

## Region gotcha

B2 buckets are region-locked. Each example notebook may interact with TWO buckets in DIFFERENT regions: the public read-only dataset bucket and the private write bucket. The `AWS_DEFAULT_REGION` / `AWS_REGION` / `AWS_ENDPOINT_URL_S3` env vars must match the **write** bucket's region (because pyarrow / boto3 use them to sign requests). The read bucket's region is handled by an explicit `S3FileSystem(endpoint_override=...)` or boto3 client constructed with the right endpoint inside the notebook itself.

Current per-bucket region map:

| Bucket | Region | Used by |
|---|---|---|
| `backblaze-samples-ci` (write) | `us-east-005` | All CI workflows |
| `b2datasets` (read) | `us-west-001` | Ray, Whisper |
| `odh-datasets` (read) | `us-west-001` | CIFAR |

If you create a new bucket, run `b2 bucket get <name>` to confirm its region before wiring it into a workflow. B2 returns a 403 with no useful error body when the SigV4 signature region doesn't match the bucket's region (B2-specific: AWS S3 would return a 301 redirect with the correct region; B2 does not).

When a notebook constructs multiple boto3 clients targeting buckets in different regions, **always pin `region_name` explicitly on each client**, even if you also set `endpoint_url`. Don't rely on the `AWS_DEFAULT_REGION` env var to disambiguate, because there is only one such env var and it can only point at one region at a time. If the region mismatches the endpoint, B2 returns the misleading error `InvalidAccessKeyId: The key '<keyId>' is not valid` (which sounds like a deleted key, but is actually a region-mismatch signal).

Capabilities on the CI application key: `listBuckets`, `listFiles`,
`readFiles`, `writeFiles`, `deleteFiles`. **Not** `writeBuckets` or
`deleteBuckets`, so the key cannot destroy the bucket itself.

## CI runtime budgeting

Notebooks that train models can blow past nbmake timeouts on GitHub Actions runners (2-core CPU, no GPU). Every notebook with a `for epoch in range(N):` loop or a `keys = list_images(...)` style dataset enumeration should gate the loop size and dataset size on env vars:

```python
EPOCHS = int(os.environ.get("<NOTEBOOK>_EPOCHS", "3"))  # human default
_max = int(os.environ.get("<NOTEBOOK>_MAX_TRAIN", "0"))
if _max > 0: train_keys = train_keys[:_max]
```

The per-notebook workflow then sets the CI values:

```yaml
env:
  <NOTEBOOK>_EPOCHS: "1"
  <NOTEBOOK>_MAX_TRAIN: "2000"
  <NOTEBOOK>_MAX_TEST: "500"
```

Goal: CI run finishes in 2-5 min. The integration is what's being tested (read seed from B2, train, write checkpoint back to B2), not model accuracy. Human users running the notebook get the full demo when they leave the env vars unset.

## Known CI gotchas

* **Ray Train v2 + Tuner reuse**: in Ray Train v2 (default in Ray 2.40+), a `TorchTrainer` instance that has already been `.fit()`-ed cannot be reused as a `Tuner` trainable (raises `TuneError: Improper 'run' - not string nor trainable.`). The ray notebook gates its optional Tune cell behind a `SKIP_TUNE_CELL` env var that CI sets to `1`; human users on local / Colab run the cell normally. Proper v2 integration (constructing a fresh trainer per Tuner trial) is a follow-up improvement, not a blocker for CI.
* **macOS PyTorch DataLoader spawn deadlock**: when `num_workers > 0` and the notebook runs inside Jupyter (or nbmake) on macOS, the DataLoader worker spawn hangs while pickling the loader + S3 client. The cifar notebook defaults `NUM_WORKERS = 0` on Darwin via `sys.platform == "darwin"`; Linux CI runs with `4`. Override with `CIFAR_NUM_WORKERS` env var.
* **PyTorch DataLoader `prefetch_factor` constraint**: PyTorch requires `prefetch_factor=None` when `num_workers=0`. The cifar notebook sets `PREFETCH_FACTOR = 2 if NUM_WORKERS > 0 else None` for this reason.
* **macOS OpenMP duplicate-runtime crash**: torch + matplotlib + numpy each ship their own libomp; macOS's dynamic linker aborts with `OMP: Error #15`. Set `KMP_DUPLICATE_LIB_OK=TRUE` in the local shell before running nbmake on macOS. Linux CI is not affected.

## Adding a new example: checklist

1. Create directory `<name>/` at repo root.
2. Author the notebook with title row + 3 badges; env-var-first fallback
   for any interactive input.
3. Write `<name>/README.md` mirroring the structure of
   `ray-train-tune-checkpoints/README.md`.
4. Write `<name>/requirements.txt`, alphabetical, matching the notebook's
   `%pip install` cell.
5. Add an entry + badges to the top-level `README.md`.
6. Add `<name>/prepare_dataset.py` if you need to stage seed data.
7. Add `.github/workflows/test-<name>.yml` mirroring
   `test-ray-train-tune.yml` with the appropriate path filter, env vars,
   and timeout.
8. Run `pre-commit run --all-files` until it passes clean.
9. Open PR. The lint workflow runs on every push; the per-notebook
   workflow runs only when the matching directory changes.
