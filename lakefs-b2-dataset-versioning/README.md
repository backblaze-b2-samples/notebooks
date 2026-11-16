# Dataset versioning with lakeFS on Backblaze B2

Branch-per-experiment dataset versioning for ML, using [lakeFS](https://lakefs.io) on top of [Backblaze B2](https://www.backblaze.com/cloud-storage). The notebook walks through a satellite-imagery scenario: ingest a tile catalog on `main`, branch to test a new cloud-mask classifier, commit the modified catalog, diff against `main`, then either merge the experiment or roll back. lakeFS handles versioning; B2 holds the actual bytes.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/backblaze-b2-samples/notebooks/blob/main/lakefs-b2-dataset-versioning/lakefs_b2_dataset_versioning.ipynb) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/lakefs-b2-dataset-versioning/lakefs_b2_dataset_versioning.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

## What's in this directory

| File | Purpose |
|---|---|
| `lakefs_b2_dataset_versioning.ipynb` | Main notebook. Generates a synthetic satellite-tile catalog as Parquet, commits it to lakeFS, branches to test a new cloud-mask classifier, compares the branch against `main`, then merges or reverts. |
| `requirements.txt` | Pip dependencies. Used by Binder (and any user who wants to recreate the env locally). |

There is no `prepare_dataset.py` here: the notebook generates its own synthetic dataset in-memory, so there is nothing to stage in B2 ahead of time. The companion sample app at [`lakefs-on-b2-quickstart`](https://github.com/backblaze-b2-samples/lakefs-on-b2-quickstart) is the only setup step required before running the notebook.

## Why this works

lakeFS sits between your application and your object store. Your code (in this notebook, the lakeFS Python SDK; in other workflows, Spark, Hadoop, or boto3) talks to a lakeFS endpoint instead of directly to B2. lakeFS:

1. Stores small commit / branch / ref metadata in its own Postgres KV.
2. Writes the actual data objects into the underlying B2 bucket via the [S3-compatible API](https://www.backblaze.com/docs/cloud-storage-s3-compatible-api).
3. Tags every outbound B2 request with a `lakefs/<version>` `User-Agent` so you can attribute traffic on the B2 side (shipped in [lakeFS 1.34](https://github.com/treeverse/lakeFS/pull/10426)).

For the notebook to reach a lakeFS server, you need one running locally. The companion repo at [`lakefs-on-b2-quickstart`](https://github.com/backblaze-b2-samples/lakefs-on-b2-quickstart) gives you a one-command Docker Compose stack:

```bash
git clone https://github.com/backblaze-b2-samples/lakefs-on-b2-quickstart.git
cd lakefs-on-b2-quickstart
cp .env.example .env
$EDITOR .env   # fill in your B2 application key + bucket
docker compose up -d
```

Once `docker compose ps` shows `lakefs-on-b2-quickstart-lakefs-1` as `(healthy)`, the notebook can connect to it at `http://localhost:8000`.

## Two distinct buckets

This is the canonical `CLAUDE.md` section, but the notebook is a deliberate exception to the repo-wide "Two-bucket pattern". lakeFS owns the dataset lifecycle, so there is a single private B2 bucket that lakeFS uses as its blockstore. The other notebooks in this repo ([Ray](../ray-train-tune-checkpoints/), [Whisper](../whisper-b2-transcription/)) use a public read bucket plus a private write bucket; this one consolidates both roles into the lakeFS blockstore. Everything the notebook reads or writes goes through lakeFS, not directly to B2.

| Bucket | Used by | Purpose |
|---|---|---|
| `${B2_LAKEFS_DATA_BUCKET}` (private) | lakeFS server (configured in `lakefs-on-b2-quickstart/.env`) | All notebook reads and writes flow through lakeFS, which lays out objects under a content-addressed prefix structure inside this bucket. |

One optional verification cell at the end uses `boto3` to peek at the actual B2 object layout for educational purposes, and (per repo convention) sets `user_agent_extra="b2-notebook-lakefs"` plus an explicit `region_name`.

## Running the notebook (and where to put credentials)

The notebook talks to lakeFS, not B2 directly. It needs the lakeFS endpoint URL, the lakeFS admin credentials that you configured in `lakefs-on-b2-quickstart/.env`, and a storage namespace where lakeFS can write the demo repo. In the common quickstart setup, that namespace is derived from `B2_LAKEFS_DATA_BUCKET`; advanced users can set `LAKEFS_NB_STORAGE_NAMESPACE` directly. Raw B2 credentials are only needed by the optional verification cell that lists objects in the bucket.

| Environment | Secret store | Notes |
|---|---|---|
| **Local Jupyter / shell** ⭐ | Shell env | The recommended setup. Start the [`lakefs-on-b2-quickstart`](https://github.com/backblaze-b2-samples/lakefs-on-b2-quickstart) stack on the same machine, then `source lakefs-on-b2-quickstart/.env` (or copy the relevant vars into your shell) and `jupyter lab lakefs_b2_dataset_versioning.ipynb`. The notebook reads `LAKEFS_ENDPOINT_URL`, `LAKEFS_ACCESS_KEY_ID`, and `LAKEFS_SECRET_ACCESS_KEY` from the environment. |
| **GitHub Codespaces** | User Settings → Codespaces → *Codespaces secrets* | Add the credentials, scope them to `backblaze-b2-samples/notebooks`. You still need a running lakeFS server reachable from the Codespace; the simplest path is to run the `lakefs-on-b2-quickstart` Compose stack inside the Codespace too (`docker compose` is preinstalled). |
| **Google Colab** | Left sidebar → 🔑 *Secrets* | Add the credentials and grant this notebook access. Note: Colab does not run Docker, so you need a lakeFS endpoint reachable from the Colab VM (e.g. via [ngrok](https://ngrok.com) tunneling localhost, or a hosted lakeFS Cloud instance). |
| **Binder** | None, ephemeral by design | Falls back to `getpass.getpass()` prompts. Same lakeFS-endpoint-reachability caveat as Colab applies. |

Standard env vars used by the notebook:

| Env var | Set to | Required for |
|---|---|---|
| `LAKEFS_ENDPOINT_URL` | `http://localhost:8000` if running the quickstart locally | All cells |
| `LAKEFS_ACCESS_KEY_ID` | `LAKEFS_ADMIN_ACCESS_KEY_ID` from the quickstart `.env` | All cells |
| `LAKEFS_SECRET_ACCESS_KEY` | `LAKEFS_ADMIN_SECRET_ACCESS_KEY` from the quickstart `.env` | All cells |
| `B2_LAKEFS_DATA_BUCKET` | Same value as in the quickstart `.env` | Repo creation, unless `LAKEFS_NB_STORAGE_NAMESPACE` is set directly; also optional verification |
| `LAKEFS_NB_STORAGE_NAMESPACE` | `s3://<bucket>/<prefix>` | Optional override for the lakeFS repo storage namespace |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Your B2 application key, same as in the quickstart `.env` | Optional verification cell |
| `AWS_ENDPOINT_URL_S3` | `https://s3.<region>.backblazeb2.com` | Optional verification cell; derived from `PRIVATE_B2_REGION` when unset |
| `PRIVATE_B2_REGION` | Region segment of the bucket, e.g. `us-east-005` | Endpoint construction and explicit B2 client region when `B2_LAKEFS_DATA_BUCKET` is set |

The notebook reads each var with `os.environ.get(..., "").strip()` and falls back to `getpass.getpass()` (for secrets) or `input()` (for the bucket name and endpoint URL) when a var is unset.

For a fully local install:

```bash
pip install -r requirements.txt
jupyter lab lakefs_b2_dataset_versioning.ipynb
```

The notebook runs end-to-end in roughly two minutes on a laptop; the synthetic dataset is small (1000 tiles, ~5 MB Parquet).

For repeat runs against the same lakeFS repo, the notebook recreates only the demo experiment branch (`experiment-cloud-mask-v2`) from the current `main` branch. The repo history still accumulates commits; use the cleanup notes at the end of the notebook if you want a fully fresh repo and B2 prefix.

## Related

* [`lakefs-on-b2-quickstart`](https://github.com/backblaze-b2-samples/lakefs-on-b2-quickstart), the companion Docker Compose stack required to run this notebook. README walks through prerequisites (Docker, a B2 bucket, an application key), startup, and a `lakectl`-based five-minute walkthrough that mirrors the notebook's lakeFS Python SDK calls one-to-one.
* [lakeFS documentation](https://docs.lakefs.io), upstream reference. Note: as of 2026-05, the documentation source is migrating to a separate repository; if a link 404s, search from <https://docs.lakefs.io> directly.
* [treeverse/lakeFS#10426](https://github.com/treeverse/lakeFS/pull/10426), the PR that added the `lakefs/<version>` `User-Agent` to every outbound S3 request from lakeFS to B2. Shipped in lakeFS 1.34.
* [Backblaze B2 Cloud Storage Application Keys](https://www.backblaze.com/docs/cloud-storage-application-keys), how to generate the keys used by lakeFS to talk to B2.
* Sibling examples in this repo: <https://github.com/backblaze-b2-samples/notebooks>.
