# Ray Train + Tune with checkpoints on Backblaze B2

End-to-end example showing how to use [Backblaze B2](https://www.backblaze.com/cloud-storage)
as both the **input data store** and the **checkpoint destination** for
distributed training with [Ray Train](https://docs.ray.io/en/latest/train/train.html)
and hyperparameter sweeps with [Ray Tune](https://docs.ray.io/en/latest/tune/index.html).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/backblaze-b2-samples/notebooks/blob/main/ray-train-tune-checkpoints/ray_train_b2.ipynb) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/ray-train-tune-checkpoints/ray_train_b2.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

## What's in this directory

| File | Purpose |
|---|---|
| `ray_train_b2.ipynb` | Main notebook. Reads California Housing parquet from a public B2 bucket, trains a small PyTorch regression model with `TorchTrainer`, writes checkpoints back to a private B2 bucket via `RunConfig(storage_path="s3://...")`, and runs an optional `Tuner` sweep over learning rates. |
| `prepare_dataset.py` | One-off script that generates the public parquet dataset from `sklearn.datasets.fetch_california_housing()` and shows the upload command for both the AWS CLI and the Backblaze `b2` CLI. |
| `requirements.txt` | Pip dependencies. Used by Binder (and any user who wants to recreate the env locally). |

## Why this works

Backblaze B2 exposes an S3-compatible API. Ray Train's storage layer goes
through `pyarrow.fs.FileSystem.from_uri` for `s3://` URIs, and pyarrow
honors the standard AWS endpoint and credential environment variables,
so B2 is a drop-in S3 replacement with no Ray code changes. Three env vars
wire it together:

| Env var | Set to |
|---|---|
| `AWS_ENDPOINT_URL_S3` | `https://s3.<region>.backblazeb2.com` (region from your B2 bucket settings) |
| `AWS_ACCESS_KEY_ID` | your B2 application key ID |
| `AWS_SECRET_ACCESS_KEY` | your B2 application key |

If you'd rather follow Backblaze's documented `B2_APPLICATION_KEY_ID` /
`B2_APPLICATION_KEY` env var names (read by the Backblaze `b2` CLI),
recent Ray releases alias them onto the AWS-named equivalents
automatically.

Generate a B2 application key at
<https://www.backblaze.com/docs/cloud-storage-application-keys>.

## Two distinct buckets

Backblaze B2 bucket privacy is set at the bucket level: a "Public" bucket
is anonymously readable but **never** publicly writable. The notebook
accordingly uses two buckets:

* **Read**, the public `b2datasets` bucket holding the demo parquet files.
  No credentials needed.
* **Write**, a *separate* private B2 bucket of yours, with an application
  key that has write access to it. This is where Ray Train checkpoints land.

## Running the notebook (and where to put credentials)

Pick the path that matches where you want to run it. For the §3 write path
the notebook needs `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`; the §2
read path is anonymous and works without them.

| Environment | Secret store | Notes |
|---|---|---|
| **GitHub Codespaces** ⭐ | User Settings → Codespaces → *Codespaces secrets* | Add `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`, scope them to `backblaze-b2-samples/notebooks`. Injected as env vars natively, cleanest setup. Click the badge above to launch. |
| **Google Colab** | Left sidebar → 🔑 *Secrets* | Add the two secrets and grant this notebook access. The notebook pulls them via `google.colab.userdata.get(...)`. |
| **Kaggle** | Add-ons → *Secrets* | Adapt the credential cell to use `UserSecretsClient().get_secret(...)`. |
| **Binder** | None, ephemeral by design | Falls back to `getpass.getpass()` to prompt at runtime. Or skip §3 and only run the read-only §1 + §2 demo. |
| **Local Jupyter / shell** | Shell env | `export AWS_ACCESS_KEY_ID=...; export AWS_SECRET_ACCESS_KEY=...` before launching, or use a `.env` file. |

The notebook tries each source in priority order: explicit env vars
(already exported / Codespaces injection) → Colab Secrets → interactive
`getpass` prompt.

For a fully local install:

```bash
pip install -r requirements.txt
jupyter lab ray_train_b2.ipynb
```

The notebook runs end-to-end on CPU; the regression model is small enough
to train in a few minutes on a laptop. The `Tuner` sweep adds another few
minutes per trial.

## Regenerating the public dataset

If you want to upload a fresh copy of the California Housing parquet to a
B2 bucket of your own, run:

```bash
pip install pandas pyarrow scikit-learn
python prepare_dataset.py --out ./california_housing
```

then upload the resulting directory to B2:

```bash
# With the AWS CLI:
aws s3 sync ./california_housing/ \
    s3://<your-bucket>/ray-train-demo/california_housing/ \
    --endpoint-url https://s3.us-west-001.backblazeb2.com

# Or with the native Backblaze b2 CLI:
b2 sync ./california_housing/ b2://<your-bucket>/ray-train-demo/california_housing/
```

## Related

* [Ray Train persistent-storage user guide](https://docs.ray.io/en/master/train/user-guides/persistent-storage.html#s3-compatible-storage-minio-backblaze-b2-etc), upstream reference for `RunConfig.storage_path` with both the URL-query-parameter and explicit-`S3FileSystem` patterns.
* [Backblaze B2 Cloud Storage Application Keys](https://www.backblaze.com/docs/cloud-storage-application-keys), how to generate the keys mapped onto the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars above.
* Sibling examples in this repo: <https://github.com/backblaze-b2-samples/notebooks>
